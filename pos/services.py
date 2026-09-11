import uuid
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db import transaction
from .models import (
    POSTerminal, POSSession, POSCustomerLoyalty, POSCouponPromotion,
    POSOrder, POSOrderItem, POSPayment, POSCashTransaction
)
from inventory.models import Product, StockMovement
from accounting.models import JournalEntry, JournalItem, Account


class POSPricingEngine:
    """
    Enterprise retail pricing engine supporting multi-tier calculations,
    promotions, discounts, customer loyalty points, and retail rounding.
    """

    @staticmethod
    def calculate_line_item(unit_price, quantity, discount_pct=Decimal('0.00'), tax_rate=Decimal('0.00')):
        unit_price = Decimal(str(unit_price))
        quantity = Decimal(str(quantity))
        discount_pct = Decimal(str(discount_pct))
        tax_rate = Decimal(str(tax_rate))

        base_amount = (unit_price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discount_amount = (base_amount * (discount_pct / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discounted_base = base_amount - discount_amount
        tax_amount = (discounted_base * (tax_rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        line_total = discounted_base + tax_amount

        return {
            'base_amount': base_amount,
            'discount_amount': discount_amount,
            'taxable_amount': discounted_base,
            'tax_amount': tax_amount,
            'line_total': line_total,
        }

    @staticmethod
    def validate_and_apply_coupon(coupon_code, order_subtotal):
        order_subtotal = Decimal(str(order_subtotal))
        try:
            coupon = POSCouponPromotion.objects.get(
                code__iexact=coupon_code.strip(),
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
        except POSCouponPromotion.DoesNotExist:
            return {'valid': False, 'message': 'Invalid or expired coupon code.', 'discount': Decimal('0.00'), 'coupon': None}

        if coupon.times_used >= coupon.usage_limit:
            return {'valid': False, 'message': 'Coupon usage limit has been reached.', 'discount': Decimal('0.00'), 'coupon': None}

        if order_subtotal < coupon.min_order_value:
            return {
                'valid': False,
                'message': f'Order total {order_subtotal} does not meet minimum requirement {coupon.min_order_value}.',
                'discount': Decimal('0.00'),
                'coupon': None
            }

        discount = Decimal('0.00')
        if coupon.discount_type == 'PERCENT':
            discount = (order_subtotal * (coupon.discount_value / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if coupon.max_discount_cap > Decimal('0.00') and discount > coupon.max_discount_cap:
                discount = coupon.max_discount_cap
        elif coupon.discount_type == 'FIXED':
            discount = min(coupon.discount_value, order_subtotal)

        return {
            'valid': True,
            'message': f'Coupon {coupon.code} applied successfully.',
            'discount': discount,
            'coupon': coupon
        }

    @staticmethod
    def calculate_loyalty_accrual(grand_total, loyalty_tier='BRONZE'):
        """
        1 point per $10 spent base rate + tier bonus
        """
        spend = Decimal(str(grand_total))
        base_points = int(spend // Decimal('10.00'))
        tier_multipliers = {
            'BRONZE': Decimal('1.00'),
            'SILVER': Decimal('1.05'),
            'GOLD': Decimal('1.10'),
            'PLATINUM': Decimal('1.20'),
        }
        multiplier = tier_multipliers.get(loyalty_tier, Decimal('1.00'))
        points_earned = int(Decimal(base_points) * multiplier)
        return max(0, points_earned)


class POSOrderProcessor:
    """
    High-performance transaction processing for retail checkouts, inventory deductions,
    split payments, and automated GL financial reconciliation.
    """

    @classmethod
    @transaction.atomic
    def process_checkout(cls, session, cashier, items_data, payments_data, customer=None, coupon_code=None, notes="", loyalty_points_to_redeem=0):
        if session.status != 'OPEN':
            raise ValueError(f"POS Session {session.session_number} is not open for checkout.")

        # 1. Calculate totals
        subtotal = Decimal('0.00')
        total_tax = Decimal('0.00')
        total_item_discount = Decimal('0.00')
        order_items_to_create = []

        for item_data in items_data:
            product = Product.objects.select_for_update().get(id=item_data['product_id'])
            qty = Decimal(str(item_data.get('quantity', 1)))
            unit_price = Decimal(str(item_data.get('unit_price', product.selling_price or product.cost_price or 0)))
            disc_pct = Decimal(str(item_data.get('discount_percentage', 0)))
            tax_rate = Decimal(str(item_data.get('tax_rate', product.tax_rate if hasattr(product, 'tax_rate') else 0)))

            calc = POSPricingEngine.calculate_line_item(unit_price, qty, disc_pct, tax_rate)
            subtotal += calc['taxable_amount']
            total_tax += calc['tax_amount']
            total_item_discount += calc['discount_amount']

            order_items_to_create.append({
                'product': product,
                'product_name': product.name,
                'sku': product.sku or '',
                'barcode': product.barcode or '',
                'unit_price': unit_price,
                'quantity': qty,
                'tax_rate': tax_rate,
                'tax_amount': calc['tax_amount'],
                'discount_percentage': disc_pct,
                'discount_amount': calc['discount_amount'],
                'line_total': calc['line_total'],
                'notes': item_data.get('notes', '')
            })

        # 2. Coupon evaluation
        coupon_obj = None
        coupon_discount = Decimal('0.00')
        if coupon_code:
            coupon_res = POSPricingEngine.validate_and_apply_coupon(coupon_code, subtotal)
            if coupon_res['valid']:
                coupon_obj = coupon_res['coupon']
                coupon_discount = coupon_res['discount']
                coupon_obj.times_used += 1
                coupon_obj.save(update_fields=['times_used'])

        # 3. Loyalty redemption ($0.05 per point)
        loyalty_discount = Decimal('0.00')
        loyalty_card = None
        if customer and hasattr(customer, 'pos_loyalty'):
            loyalty_card = customer.pos_loyalty
            if loyalty_points_to_redeem > 0 and loyalty_card.points_balance >= loyalty_points_to_redeem:
                loyalty_discount = Decimal(loyalty_points_to_redeem) * Decimal('0.05')
                loyalty_card.points_balance -= loyalty_points_to_redeem
                loyalty_card.lifetime_points_redeemed += loyalty_points_to_redeem
                loyalty_card.save()

        # 4. Net totals & Rounding
        total_discount = total_item_discount + coupon_discount + loyalty_discount
        gross_total = (subtotal - coupon_discount - loyalty_discount) + total_tax
        if gross_total < Decimal('0.00'):
            gross_total = Decimal('0.00')

        grand_total = gross_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        roundoff_amount = grand_total - gross_total

        # 5. Create Order
        order_num = f"POS-{session.terminal.terminal_code}-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        pos_order = POSOrder.objects.create(
            order_number=order_num,
            session=session,
            terminal=session.terminal,
            cashier=cashier,
            customer=customer,
            coupon=coupon_obj,
            order_type='RETAIL',
            status='COMPLETED',
            subtotal=subtotal,
            tax_amount=total_tax,
            discount_amount=total_discount,
            roundoff_amount=roundoff_amount,
            grand_total=grand_total,
            loyalty_points_redeemed=loyalty_points_to_redeem,
            loyalty_discount_applied=loyalty_discount,
            notes=notes
        )

        # 6. Save items and update inventory movements
        for itm in order_items_to_create:
            product = itm['product']
            POSOrderItem.objects.create(
                order=pos_order,
                product=product,
                product_name=itm['product_name'],
                sku=itm['sku'],
                barcode=itm['barcode'],
                unit_price=itm['unit_price'],
                quantity=itm['quantity'],
                tax_rate=itm['tax_rate'],
                tax_amount=itm['tax_amount'],
                discount_percentage=itm['discount_percentage'],
                discount_amount=itm['discount_amount'],
                line_total=itm['line_total'],
                notes=itm['notes']
            )

            # Reduce product inventory
            if session.terminal.warehouse:
                product.current_stock = max(Decimal('0.000'), Decimal(str(product.current_stock)) - itm['quantity'])
                product.save(update_fields=['current_stock'])
                StockMovement.objects.create(
                    product=product,
                    warehouse_name=session.terminal.warehouse.name if session.terminal.warehouse else 'Main Retail Store',
                    movement_type='SALES_DELIVERY',
                    quantity=itm['quantity'],
                    unit_cost=product.cost_price or Decimal('0.00'),
                    total_cost=(product.cost_price or Decimal('0.00')) * itm['quantity'],
                    balance_after=product.current_stock,
                    reference_number=f"POS: {pos_order.order_number}",
                    created_by=cashier
                )

        # 7. Payments
        paid_sum = Decimal('0.00')
        cash_paid = Decimal('0.00')
        for pay in payments_data:
            p_amount = Decimal(str(pay['amount']))
            p_method = pay.get('payment_method', 'CASH')
            paid_sum += p_amount
            if p_method == 'CASH':
                cash_paid += p_amount

            POSPayment.objects.create(
                order=pos_order,
                session=session,
                payment_method=p_method,
                amount=p_amount,
                reference_number=pay.get('reference_number', ''),
                card_last4=pay.get('card_last4', ''),
                card_network=pay.get('card_network', ''),
                auth_code=pay.get('auth_code', ''),
                status='SUCCESS'
            )

        change_due = max(Decimal('0.00'), paid_sum - grand_total)
        pos_order.paid_amount = paid_sum
        pos_order.change_returned = change_due

        # 8. Loyalty points accrual
        if customer:
            if not loyalty_card:
                loyalty_card, _ = POSCustomerLoyalty.objects.get_or_create(customer=customer)
            earned_pts = POSPricingEngine.calculate_loyalty_accrual(grand_total, loyalty_card.tier)
            loyalty_card.points_balance += earned_pts
            loyalty_card.lifetime_points_earned += earned_pts
            loyalty_card.lifetime_spend += grand_total
            loyalty_card.save()
            pos_order.loyalty_points_earned = earned_pts

        pos_order.save()

        # 9. Update Session counters
        session.total_sales_amount += grand_total
        session.total_tax_amount += total_tax
        session.total_discount_amount += total_discount
        session.total_orders_count += 1
        session.expected_cash += (cash_paid - change_due)
        session.save()

        # 10. Post Accounting Ledger entries
        cls.post_to_general_ledger(pos_order)

        return pos_order

    @classmethod
    def post_to_general_ledger(cls, order):
        """
        Creates automatic balanced Journal Entry for POS sales:
        Debit: Cash / Bank (Asset)
        Credit: Sales Revenue (Revenue)
        Credit: Sales Tax Payable (Liability)
        """
        try:
            cash_account = order.terminal.cash_account or Account.objects.filter(account_type='ASSET', name__icontains='Cash').first()
            sales_account = Account.objects.filter(account_type='REVENUE').first()
            tax_account = Account.objects.filter(account_type='LIABILITY', name__icontains='Tax').first()

            if not (cash_account and sales_account):
                return None

            entry_num = f"JE-POS-{order.order_number}"
            je = JournalEntry.objects.create(
                entry_number=entry_num,
                date=timezone.now().date(),
                reference=f"POS: {order.order_number}",
                narration=f"Automated POS Cashier revenue posting for order {order.order_number}",
                total_debit=order.grand_total,
                total_credit=order.grand_total,
                status='POSTED',
                created_by=order.cashier
            )

            # Debit Cash/Receivables
            JournalItem.objects.create(
                journal_entry=je,
                account=cash_account,
                debit=order.grand_total,
                credit=Decimal('0.00'),
                description=f"POS collections from {order.order_number}"
            )

            # Credit Revenue
            net_revenue = order.grand_total - order.tax_amount
            JournalItem.objects.create(
                journal_entry=je,
                account=sales_account,
                debit=Decimal('0.00'),
                credit=net_revenue,
                description=f"Retail sales revenue from {order.order_number}"
            )

            # Credit Tax if applicable
            if order.tax_amount > Decimal('0.00') and tax_account:
                JournalItem.objects.create(
                    journal_entry=je,
                    account=tax_account,
                    debit=Decimal('0.00'),
                    credit=order.tax_amount,
                    description=f"Sales tax collected on {order.order_number}"
                )

            return je
        except Exception:
            # Non-blocking for offline or dev environments
            return None


class POSSessionManager:
    """
    Handles shift open, mid-shift cash drops, X-Reading, and shift close with Z-Report.
    """

    @staticmethod
    def open_session(terminal, cashier, opening_cash, notes=""):
        # Ensure no active open session on this terminal
        active_sess = POSSession.objects.filter(terminal=terminal, status='OPEN').first()
        if active_sess:
            raise ValueError(f"Terminal {terminal.terminal_code} already has an active open session (#{active_sess.session_number}).")

        opening_cash = Decimal(str(opening_cash))
        sess_num = f"SESS-{terminal.terminal_code}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        session = POSSession.objects.create(
            session_number=sess_num,
            terminal=terminal,
            cashier=cashier,
            opening_cash=opening_cash,
            expected_cash=opening_cash,
            counted_cash=Decimal('0.00'),
            cash_difference=Decimal('0.00'),
            status='OPEN',
            opening_notes=notes
        )
        return session

    @staticmethod
    def record_cash_transaction(session, txn_type, amount, reason, authorized_by):
        amount = Decimal(str(amount))
        txn = POSCashTransaction.objects.create(
            session=session,
            transaction_type=txn_type,
            amount=amount,
            reason=reason,
            authorized_by=authorized_by
        )
        if txn_type in ['CASH_IN']:
            session.expected_cash += amount
        elif txn_type in ['CASH_OUT', 'SAFE_DROP', 'PETTY_EXPENSE']:
            session.expected_cash -= amount
        session.save()
        return txn

    @staticmethod
    @transaction.atomic
    def close_session(session, counted_cash, closing_notes="", closed_by=None):
        if session.status != 'OPEN':
            raise ValueError("Only open sessions can be closed.")

        counted_cash = Decimal(str(counted_cash))
        diff = counted_cash - session.expected_cash

        session.counted_cash = counted_cash
        session.cash_difference = diff
        session.closing_time = timezone.now()
        session.status = 'CLOSED'
        session.closing_notes = closing_notes
        session.closed_by = closed_by or session.cashier
        session.save()

        return session

    @staticmethod
    def generate_z_report_data(session):
        payments = POSPayment.objects.filter(session=session, status='SUCCESS')
        payment_breakdown = {}
        for p in payments:
            payment_breakdown[p.payment_method] = payment_breakdown.get(p.payment_method, Decimal('0.00')) + p.amount

        cash_txns = POSCashTransaction.objects.filter(session=session)
        cash_ins = sum((t.amount for t in cash_txns if t.transaction_type == 'CASH_IN'), Decimal('0.00'))
        cash_outs = sum((t.amount for t in cash_txns if t.transaction_type in ['CASH_OUT', 'SAFE_DROP', 'PETTY_EXPENSE']), Decimal('0.00'))

        return {
            'session': session,
            'terminal': session.terminal,
            'cashier': session.cashier,
            'opening_time': session.opening_time,
            'closing_time': session.closing_time or timezone.now(),
            'opening_cash': session.opening_cash,
            'expected_cash': session.expected_cash,
            'counted_cash': session.counted_cash,
            'cash_difference': session.cash_difference,
            'total_sales': session.total_sales_amount,
            'total_tax': session.total_tax_amount,
            'total_discount': session.total_discount_amount,
            'orders_count': session.total_orders_count,
            'payment_breakdown': payment_breakdown,
            'cash_ins': cash_ins,
            'cash_outs': cash_outs,
            'is_closed': session.status == 'CLOSED'
        }


class POSThermalReceiptFormatter:
    """
    Formats clean 80mm/58mm thermal printable receipts and raw ESC/POS commands.
    """

    @staticmethod
    def generate_text_receipt(order):
        line_separator = "=" * 42
        dash_separator = "-" * 42

        lines = [
            order.terminal.receipt_header.center(42),
            line_separator,
            f"Terminal: {order.terminal.terminal_code}".ljust(21) + f"Order: {order.order_number[-8:]}".rjust(21),
            f"Cashier: {order.cashier.get_full_name() or order.cashier.username}".ljust(21) + f"Date: {order.created_at.strftime('%d/%m/%y %H:%M')}".rjust(21),
            f"Customer: {order.customer.name if order.customer else 'Walk-In Customer'}",
            dash_separator,
            "ITEM                  QTY    PRICE   TOTAL",
            dash_separator,
        ]

        for item in order.items.all():
            name = (item.product_name[:18] + '..') if len(item.product_name) > 20 else item.product_name.ljust(20)
            qty_str = f"{item.quantity:g}".rjust(4)
            price_str = f"{item.unit_price:.2f}".rjust(7)
            total_str = f"{item.line_total:.2f}".rjust(8)
            lines.append(f"{name} {qty_str} {price_str} {total_str}")

        lines.extend([
            dash_separator,
            f"Subtotal:".ljust(30) + f"{order.subtotal:.2f}".rjust(12),
            f"Tax:".ljust(30) + f"{order.tax_amount:.2f}".rjust(12),
            f"Discount:".ljust(30) + f"-{order.discount_amount:.2f}".rjust(12),
            f"Round-off:".ljust(30) + f"{order.roundoff_amount:.2f}".rjust(12),
            line_separator,
            f"GRAND TOTAL:".ljust(28) + f"${order.grand_total:.2f}".rjust(14),
            line_separator,
            "PAYMENTS:",
        ])

        for p in order.payments.all():
            lines.append(f"  {p.get_payment_method_display()}:".ljust(30) + f"${p.amount:.2f}".rjust(12))

        lines.append(f"Change Returned:".ljust(30) + f"${order.change_returned:.2f}".rjust(12))

        if order.loyalty_points_earned:
            lines.append(f"Loyalty Points Earned: +{order.loyalty_points_earned} pts")

        lines.extend([
            dash_separator,
            order.terminal.receipt_footer.center(42),
            line_separator
        ])

        return "\n".join(lines)
