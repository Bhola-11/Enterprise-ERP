import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import (
    B2BAccount, B2BCatalogPriceTier, QuoteApprovalRequest,
    SelfServiceOrder, SelfServiceOrderItem, DigitalPaymentTransaction
)
from .forms import B2BAccountForm, PriceTierForm, QuoteActionForm, QuickOrderForm, PaymentCheckoutForm
from .services import B2BPricingEngine, CreditCheckService, DigitalPaymentGateway, QuoteConversionService
from sales.models import Customer, Quotation, SalesOrder, Invoice
from inventory.models import Product

@login_required
def dashboard_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    b2b_accounts = B2BAccount.objects.filter(organization=org) if org else B2BAccount.objects.all()
    
    total_accounts = b2b_accounts.count()
    total_credit_granted = b2b_accounts.aggregate(Sum('credit_limit'))['credit_limit__sum'] or Decimal('0.00')
    total_credit_used = b2b_accounts.aggregate(Sum('credit_balance_used'))['credit_balance_used__sum'] or Decimal('0.00')
    
    pending_quotes = QuoteApprovalRequest.objects.filter(status='PENDING')
    if org:
        pending_quotes = pending_quotes.filter(organization=org)
        
    recent_orders = SelfServiceOrder.objects.filter(organization=org) if org else SelfServiceOrder.objects.all()
    recent_orders = recent_orders.order_by('-created_at')[:5]
    
    recent_payments = DigitalPaymentTransaction.objects.filter(organization=org) if org else DigitalPaymentTransaction.objects.all()
    recent_payments = recent_payments.order_by('-created_at')[:5]

    context = {
        'total_accounts': total_accounts,
        'total_credit_granted': total_credit_granted,
        'total_credit_used': total_credit_used,
        'available_credit_pool': max(Decimal('0.00'), total_credit_granted - total_credit_used),
        'pending_quotes_count': pending_quotes.count(),
        'pending_quotes': pending_quotes[:5],
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'b2b_accounts': b2b_accounts[:5],
    }
    return render(request, 'b2b_portal/dashboard.html', context)


@login_required
def catalog_list_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    products = Product.objects.filter(organization=org, is_active=True) if org else Product.objects.filter(is_active=True)
    
    account_id = request.GET.get('account_id')
    selected_account = None
    if account_id:
        selected_account = B2BAccount.objects.filter(id=account_id).first()
    if not selected_account:
        selected_account = B2BAccount.objects.filter(organization=org).first() if org else B2BAccount.objects.first()

    catalog_data = []
    for p in products[:30]:
        tier_pricing = B2BPricingEngine.resolve_item_price(selected_account, p, quantity=10) if selected_account else {
            'unit_price': getattr(p, 'selling_price', Decimal('100.00')),
            'discount_percentage': Decimal('0.00'),
            'discount_amount': Decimal('0.00'),
            'final_unit_price': getattr(p, 'selling_price', Decimal('100.00')),
            'subtotal': getattr(p, 'selling_price', Decimal('100.00')) * 10
        }
        catalog_data.append({
            'product': p,
            'pricing': tier_pricing,
            'sku': getattr(p, 'sku', f'SKU-{p.id}'),
            'stock': getattr(p, 'stock_quantity', 150)
        })

    accounts = B2BAccount.objects.filter(organization=org) if org else B2BAccount.objects.all()
    context = {
        'catalog_data': catalog_data,
        'accounts': accounts,
        'selected_account': selected_account
    }
    return render(request, 'b2b_portal/catalog.html', context)


@login_required
def quick_order_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    b2b_account = B2BAccount.objects.filter(organization=org).first() if org else B2BAccount.objects.first()

    if request.method == 'POST':
        form = QuickOrderForm(request.POST, organization=org)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            po_ref = form.cleaned_data['po_reference']
            shipping_addr = form.cleaned_data['shipping_address']
            req_date = form.cleaned_data['requested_date']

            pricing = B2BPricingEngine.resolve_item_price(b2b_account, product, quantity)
            tax_rate = Decimal('0.08')
            tax_amount = round(pricing['subtotal'] * tax_rate, 2)
            total_amount = pricing['subtotal'] + tax_amount

            # Check credit
            if b2b_account:
                credit_eval = CreditCheckService.evaluate_credit_availability(b2b_account, total_amount)
                if not credit_eval['has_sufficient_credit']:
                    messages.error(request, f"Credit line exceeded! Shortfall: ${credit_eval['shortfall']}. Available: ${credit_eval['available_credit']}.")
                    return render(request, 'b2b_portal/quick_order.html', {'form': form, 'b2b_account': b2b_account})

            order_num = f"B2B-ORD-{uuid.uuid4().hex[:8].upper()}"
            order = SelfServiceOrder.objects.create(
                organization=org if org else (b2b_account.organization if b2b_account else None),
                b2b_account=b2b_account,
                order_number=order_num,
                po_reference_number=po_ref,
                status='SUBMITTED',
                subtotal_amount=pricing['subtotal'],
                tax_amount=tax_amount,
                total_amount=total_amount,
                shipping_address=shipping_addr,
                billing_address=shipping_addr,
                requested_delivery_date=req_date
            )
            SelfServiceOrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=pricing['final_unit_price'],
                discount_amount=pricing['discount_amount'] * quantity,
                subtotal=pricing['subtotal']
            )
            if b2b_account:
                CreditCheckService.reserve_credit(b2b_account, total_amount)
            messages.success(request, f"B2B Order {order_num} successfully created and submitted to logistics!")
            return redirect('b2b_portal:order_history')
    else:
        form = QuickOrderForm(organization=org, initial={
            'requested_date': (timezone.now() + timezone.timedelta(days=7)).date(),
            'shipping_address': 'Corporate Receiving Bay 4, 100 Industrial Pkwy, Austin TX 78701'
        })

    context = {
        'form': form,
        'b2b_account': b2b_account
    }
    return render(request, 'b2b_portal/quick_order.html', context)


@login_required
def quote_detail_view(request, pk):
    approval_request = get_object_or_404(QuoteApprovalRequest, pk=pk)

    if request.method == 'POST':
        form = QuoteActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data['notes']
            if action == 'APPROVE':
                so = QuoteConversionService.approve_and_convert(approval_request, user=request.user, customer_notes=notes)
                messages.success(request, f"Quotation approved! Auto-generated Sales Order #{so.order_number}.")
            else:
                approval_request.status = 'REJECTED'
                approval_request.rejection_reason = notes
                approval_request.decided_at = timezone.now()
                approval_request.decided_by = request.user
                approval_request.save()
                messages.info(request, f"Quotation #{approval_request.quotation.quote_number} rejected.")
            return redirect('b2b_portal:dashboard')
    else:
        form = QuoteActionForm()

    context = {
        'approval_request': approval_request,
        'quotation': approval_request.quotation,
        'items': approval_request.quotation.items.all() if hasattr(approval_request.quotation, 'items') else [],
        'form': form
    }
    return render(request, 'b2b_portal/quote_detail.html', context)


@login_required
def order_history_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    orders = SelfServiceOrder.objects.filter(organization=org) if org else SelfServiceOrder.objects.all()
    context = {'orders': orders}
    return render(request, 'b2b_portal/order_history.html', context)


@login_required
def invoice_payment_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    b2b_account = B2BAccount.objects.filter(organization=org).first() if org else B2BAccount.objects.first()
    
    invoices = Invoice.objects.filter(customer=b2b_account.customer) if (b2b_account and hasattr(b2b_account, 'customer')) else Invoice.objects.all()
    transactions = DigitalPaymentTransaction.objects.filter(b2b_account=b2b_account) if b2b_account else DigitalPaymentTransaction.objects.all()

    if request.method == 'POST':
        form = PaymentCheckoutForm(request.POST)
        if form.is_valid():
            gateway = form.cleaned_data['gateway']
            amount = form.cleaned_data['amount']
            inv_id = request.POST.get('invoice_id')
            invoice = Invoice.objects.filter(id=inv_id).first() if inv_id else None

            if b2b_account:
                tx = DigitalPaymentGateway.execute_payment(
                    b2b_account=b2b_account,
                    amount=amount,
                    gateway=gateway,
                    invoice=invoice,
                    user=request.user
                )
                messages.success(request, f"Payment of ${amount} processed successfully via {gateway}! Reference: {tx.transaction_reference}")
            return redirect('b2b_portal:invoice_payment')
    else:
        form = PaymentCheckoutForm(initial={'amount': Decimal('5000.00')})

    context = {
        'b2b_account': b2b_account,
        'invoices': invoices[:10],
        'transactions': transactions[:10],
        'form': form
    }
    return render(request, 'b2b_portal/invoice_payment.html', context)


@login_required
def account_settings_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    b2b_account = B2BAccount.objects.filter(organization=org).first() if org else B2BAccount.objects.first()

    if request.method == 'POST':
        form = B2BAccountForm(request.POST, instance=b2b_account)
        if form.is_valid():
            form.save()
            messages.success(request, "B2B account settings updated successfully!")
            return redirect('b2b_portal:account_settings')
    else:
        form = B2BAccountForm(instance=b2b_account)

    tiers = B2BCatalogPriceTier.objects.filter(b2b_account=b2b_account) if b2b_account else []
    context = {
        'b2b_account': b2b_account,
        'form': form,
        'tiers': tiers
    }
    return render(request, 'b2b_portal/account_settings.html', context)
