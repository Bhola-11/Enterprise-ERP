import uuid
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import (
    B2BAccount, B2BCatalogPriceTier, QuoteApprovalRequest,
    SelfServiceOrder, SelfServiceOrderItem, DigitalPaymentTransaction
)
from sales.models import SalesOrder, SalesOrderItem, Payment

class B2BPricingEngine:
    @staticmethod
    def resolve_item_price(b2b_account, product, quantity=1):
        tier = None
        if b2b_account:
            tier = B2BCatalogPriceTier.objects.filter(
                organization=b2b_account.organization,
                b2b_account=b2b_account,
                product=product,
                min_quantity__lte=quantity,
                is_active=True
            ).order_by('-min_quantity').first()

            if not tier:
                tier = B2BCatalogPriceTier.objects.filter(
                    organization=b2b_account.organization,
                    b2b_account__isnull=True,
                    product=product,
                    min_quantity__lte=quantity,
                    is_active=True
                ).order_by('-min_quantity').first()

        if tier:
            unit_price = tier.tier_unit_price
            discount_pct = tier.discount_percentage
        else:
            unit_price = getattr(product, 'selling_price', Decimal('100.00'))
            discount_pct = Decimal('0.00')

        if discount_pct > Decimal('0.00'):
            discount_amount = unit_price * (discount_pct / Decimal('100.0'))
            final_unit_price = unit_price - discount_amount
        else:
            discount_amount = Decimal('0.00')
            final_unit_price = unit_price

        subtotal = round(final_unit_price * Decimal(quantity), 2)
        return {
            'unit_price': unit_price,
            'discount_percentage': discount_pct,
            'discount_amount': round(discount_amount, 2),
            'final_unit_price': round(final_unit_price, 2),
            'subtotal': subtotal
        }

    @staticmethod
    def calculate_order_totals(b2b_account, line_items_data, tax_rate=Decimal('0.08')):
        subtotal = Decimal('0.00')
        processed_lines = []

        for item in line_items_data:
            pricing = B2BPricingEngine.resolve_item_price(
                b2b_account, item['product'], item['quantity']
            )
            subtotal += pricing['subtotal']
            processed_lines.append({
                'product': item['product'],
                'quantity': item['quantity'],
                'unit_price': pricing['final_unit_price'],
                'discount_amount': pricing['discount_amount'] * item['quantity'],
                'subtotal': pricing['subtotal']
            })

        tax_amount = round(subtotal * tax_rate, 2)
        total_amount = subtotal + tax_amount
        return {
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'lines': processed_lines
        }


class CreditCheckService:
    @staticmethod
    def evaluate_credit_availability(b2b_account, required_amount):
        available = b2b_account.available_credit
        has_sufficient_credit = available >= Decimal(str(required_amount))
        return {
            'has_sufficient_credit': has_sufficient_credit,
            'credit_limit': b2b_account.credit_limit,
            'credit_balance_used': b2b_account.credit_balance_used,
            'available_credit': available,
            'required_amount': Decimal(str(required_amount)),
            'shortfall': max(Decimal('0.00'), Decimal(str(required_amount)) - available)
        }

    @staticmethod
    @transaction.atomic
    def reserve_credit(b2b_account, amount):
        b2b_account.credit_balance_used += Decimal(str(amount))
        b2b_account.save(update_fields=['credit_balance_used', 'updated_at'])
        return b2b_account.credit_balance_used

    @staticmethod
    @transaction.atomic
    def release_credit(b2b_account, amount):
        b2b_account.credit_balance_used = max(
            Decimal('0.00'),
            b2b_account.credit_balance_used - Decimal(str(amount))
        )
        b2b_account.save(update_fields=['credit_balance_used', 'updated_at'])
        return b2b_account.credit_balance_used


class DigitalPaymentGateway:
    @staticmethod
    @transaction.atomic
    def execute_payment(b2b_account, amount, gateway='STRIPE', invoice=None, user=None):
        tx_ref = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        gateway_tx_id = f"gw_{gateway.lower()}_{uuid.uuid4().hex[:16]}"

        tx = DigitalPaymentTransaction.objects.create(
            organization=b2b_account.organization,
            b2b_account=b2b_account,
            invoice=invoice,
            transaction_reference=tx_ref,
            payment_gateway=gateway,
            gateway_transaction_id=gateway_tx_id,
            amount=Decimal(str(amount)),
            currency='USD',
            status='CAPTURED',
            completed_at=timezone.now(),
            response_payload={
                'status': 'succeeded',
                'gateway_code': '200_OK',
                'gateway_reference': gateway_tx_id,
                'authorized_by': user.username if user else 'system_gateway'
            }
        )

        if invoice:
            try:
                gl_payment = Payment.objects.create(
                    invoice=invoice,
                    customer=invoice.customer,
                    payment_number=f"PAY-{tx_ref}",
                    payment_date=timezone.now().date(),
                    amount=Decimal(str(amount)),
                    payment_method='CREDIT_CARD',
                    reference_number=tx_ref,
                    notes=f"Processed via B2B Gateway ({gateway})"
                )
                tx.posted_gl_payment = gl_payment
                tx.save(update_fields=['posted_gl_payment'])
            except Exception:
                pass

        CreditCheckService.release_credit(b2b_account, amount)
        return tx


class QuoteConversionService:
    @staticmethod
    @transaction.atomic
    def approve_and_convert(approval_request, user=None, customer_notes=""):
        approval_request.status = 'APPROVED'
        approval_request.customer_notes = customer_notes
        approval_request.decided_at = timezone.now()
        approval_request.decided_by = user
        approval_request.save()

        quotation = approval_request.quotation
        quotation.status = 'ACCEPTED'
        quotation.save(update_fields=['status'])

        q_num = getattr(quotation, 'quote_number', f"QT-{quotation.id}")
        so_num = f"SO-B2B-{q_num.replace('QT-', '').replace('Q-', '')}"
        sales_order, _ = SalesOrder.objects.get_or_create(
            order_number=so_num,
            defaults={
                'customer': quotation.customer,
                'quotation': quotation,
                'order_date': timezone.now().date(),
                'status': 'CONFIRMED',
                'subtotal': quotation.subtotal,
                'tax_amount': quotation.tax_amount,
                'total_amount': quotation.total_amount,
                'notes': f"Auto-converted from Quote #{q_num}"
            }
        )

        approval_request.resulting_sales_order = sales_order
        approval_request.status = 'CONVERTED'
        approval_request.save(update_fields=['resulting_sales_order', 'status'])
        return sales_order
