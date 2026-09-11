import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Q, Sum
from django.utils import timezone

from .models import (
    POSTerminal, POSSession, POSOrder, POSOrderItem,
    POSPayment, POSCashTransaction, POSCouponPromotion, POSCustomerLoyalty
)
from .forms import (
    POSTerminalForm, POSSessionOpenForm, POSSessionCloseForm,
    POSCashTransactionForm, POSCouponForm
)
from .services import (
    POSOrderProcessor, POSSessionManager, POSThermalReceiptFormatter,
    POSPricingEngine
)
from inventory.models import Product, ProductCategory
from sales.models import Customer


@login_required
def terminal_list(request):
    terminals = POSTerminal.objects.select_related('branch', 'warehouse').all()
    # Annotate with active session info
    active_sessions = {s.terminal_id: s for s in POSSession.objects.filter(status='OPEN')}
    for term in terminals:
        term.active_session = active_sessions.get(term.id)

    context = {
        'terminals': terminals,
        'page_title': 'Point of Sale Terminals',
    }
    return render(request, 'pos/terminal_list.html', context)


@login_required
def terminal_create(request):
    if request.method == 'POST':
        form = POSTerminalForm(request.POST)
        if form.is_valid():
            term = form.save()
            messages.success(request, f"Terminal {term.terminal_code} created successfully.")
            return redirect('pos:terminal_list')
    else:
        form = POSTerminalForm()
    return render(request, 'pos/terminal_form.html', {'form': form, 'page_title': 'Add POS Terminal'})


@login_required
def terminal_update(request, pk):
    term = get_object_or_404(POSTerminal, pk=pk)
    if request.method == 'POST':
        form = POSTerminalForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            messages.success(request, f"Terminal {term.terminal_code} updated successfully.")
            return redirect('pos:terminal_list')
    else:
        form = POSTerminalForm(instance=term)
    return render(request, 'pos/terminal_form.html', {'form': form, 'terminal': term, 'page_title': f'Edit Terminal: {term.terminal_code}'})


@login_required
def session_open(request, terminal_id):
    terminal = get_object_or_404(POSTerminal, pk=terminal_id)
    existing_session = POSSession.objects.filter(terminal=terminal, status='OPEN').first()
    if existing_session:
        messages.info(request, f"Terminal already has an active session. Resuming cashier register.")
        return redirect('pos:register', session_id=existing_session.id)

    if request.method == 'POST':
        form = POSSessionOpenForm(request.POST)
        if form.is_valid():
            opening_cash = form.cleaned_data['opening_cash']
            notes = form.cleaned_data['opening_notes']
            try:
                session = POSSessionManager.open_session(
                    terminal=terminal,
                    cashier=request.user,
                    opening_cash=opening_cash,
                    notes=notes
                )
                messages.success(request, f"POS Session opened successfully with float ${opening_cash}.")
                return redirect('pos:register', session_id=session.id)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = POSSessionOpenForm(initial={'opening_cash': Decimal('100.00')})

    return render(request, 'pos/session_open.html', {
        'form': form,
        'terminal': terminal,
        'page_title': f'Open Shift Session - {terminal.name}'
    })


@login_required
def session_close(request, session_id):
    session = get_object_or_404(POSSession, pk=session_id)
    if session.status != 'OPEN':
        messages.warning(request, "This session is already closed.")
        return redirect('pos:z_report', session_id=session.id)

    z_data = POSSessionManager.generate_z_report_data(session)

    if request.method == 'POST':
        form = POSSessionCloseForm(request.POST)
        if form.is_valid():
            counted_cash = form.cleaned_data['counted_cash']
            notes = form.cleaned_data['closing_notes']
            try:
                POSSessionManager.close_session(
                    session=session,
                    counted_cash=counted_cash,
                    closing_notes=notes,
                    closed_by=request.user
                )
                messages.success(request, f"Session #{session.session_number} closed and reconciled successfully.")
                return redirect('pos:z_report', session_id=session.id)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = POSSessionCloseForm(initial={'counted_cash': session.expected_cash})

    return render(request, 'pos/session_close.html', {
        'form': form,
        'session': session,
        'z_data': z_data,
        'page_title': f'Close Shift & Reconcile - Session {session.session_number}'
    })


@login_required
def session_detail(request, session_id):
    session = get_object_or_404(POSSession.objects.select_related('terminal', 'cashier', 'closed_by'), pk=session_id)
    orders = session.orders.select_related('customer').prefetch_related('items', 'payments').order_by('-created_at')
    cash_txns = session.cash_transactions.select_related('authorized_by').all()
    z_data = POSSessionManager.generate_z_report_data(session)

    return render(request, 'pos/session_detail.html', {
        'session': session,
        'orders': orders,
        'cash_txns': cash_txns,
        'z_data': z_data,
        'page_title': f'POS Session #{session.session_number}'
    })


@login_required
def z_report(request, session_id):
    session = get_object_or_404(POSSession, pk=session_id)
    z_data = POSSessionManager.generate_z_report_data(session)
    return render(request, 'pos/z_report.html', {
        'session': session,
        'z_data': z_data,
        'page_title': f'Z-Report / Daily Shift Audit - {session.session_number}'
    })


@login_required
def register(request, session_id):
    session = get_object_or_404(POSSession.objects.select_related('terminal', 'cashier'), pk=session_id)
    if session.status != 'OPEN':
        messages.warning(request, "This session is closed. Please open a new session to use the cashier.")
        return redirect('pos:terminal_list')

    categories = ProductCategory.objects.all()
    products = Product.objects.filter(is_active=True).select_related('category')[:60]
    customers = Customer.objects.filter(is_active=True)[:100]

    context = {
        'session': session,
        'terminal': session.terminal,
        'categories': categories,
        'products': products,
        'customers': customers,
        'page_title': f'Cashier Terminal - {session.terminal.name}',
    }
    return render(request, 'pos/register.html', context)


@login_required
def order_history(request):
    query = request.GET.get('q', '')
    terminal_id = request.GET.get('terminal', '')
    status = request.GET.get('status', '')

    orders = POSOrder.objects.select_related('terminal', 'cashier', 'customer').order_by('-created_at')

    if query:
        orders = orders.filter(Q(order_number__icontains=query) | Q(customer__name__icontains=query) | Q(customer__phone__icontains=query))
    if terminal_id:
        orders = orders.filter(terminal_id=terminal_id)
    if status:
        orders = orders.filter(status=status)

    terminals = POSTerminal.objects.all()
    return render(request, 'pos/order_history.html', {
        'orders': orders[:100],
        'terminals': terminals,
        'query': query,
        'selected_terminal': terminal_id,
        'selected_status': status,
        'page_title': 'POS Sales & Receipts History'
    })


@login_required
def order_receipt(request, order_id):
    order = get_object_or_404(
        POSOrder.objects.select_related('terminal', 'cashier', 'customer', 'coupon').prefetch_related('items', 'payments'),
        pk=order_id
    )
    raw_text = POSThermalReceiptFormatter.generate_text_receipt(order)

    if request.GET.get('format') == 'raw':
        return HttpResponse(raw_text, content_type='text/plain')

    return render(request, 'pos/receipt_thermal.html', {
        'order': order,
        'raw_text': raw_text,
        'page_title': f'Receipt - {order.order_number}'
    })


@login_required
def cash_transaction_create(request, session_id):
    session = get_object_or_404(POSSession, pk=session_id)
    if request.method == 'POST':
        form = POSCashTransactionForm(request.POST)
        if form.is_valid():
            txn_type = form.cleaned_data['transaction_type']
            amount = form.cleaned_data['amount']
            reason = form.cleaned_data['reason']
            POSSessionManager.record_cash_transaction(
                session=session,
                txn_type=txn_type,
                amount=amount,
                reason=reason,
                authorized_by=request.user
            )
            messages.success(request, f"Cash transaction ({txn_type}) of ${amount} recorded.")
            return redirect('pos:register', session_id=session.id)
    else:
        form = POSCashTransactionForm()

    return render(request, 'pos/cash_transaction_form.html', {
        'form': form,
        'session': session,
        'page_title': 'Cash In / Cash Out Drawer Movement'
    })


# ---------------- API Endpoints for Interactive Register UI ----------------

@login_required
@require_GET
def api_product_search(request):
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category_id')

    products_qs = Product.objects.filter(is_active=True)
    if category_id:
        products_qs = products_qs.filter(category_id=category_id)
    if q:
        products_qs = products_qs.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(barcode__iexact=q)
        )

    data = []
    for p in products_qs[:30]:
        data.append({
            'id': p.id,
            'name': p.name,
            'sku': p.sku or '',
            'barcode': p.barcode or '',
            'price': float(p.selling_price if hasattr(p, 'selling_price') and p.selling_price else (p.cost_price or 0)),
            'stock': float(p.current_stock if hasattr(p, 'current_stock') and p.current_stock is not None else 0),
            'tax_rate': float(p.tax_rate if hasattr(p, 'tax_rate') and p.tax_rate else 0.0),
            'category': p.category.name if p.category else 'General',
        })
    return JsonResponse({'success': True, 'products': data})


@login_required
@require_GET
def api_customer_loyalty(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    loyalty, _ = POSCustomerLoyalty.objects.get_or_create(customer=customer)
    return JsonResponse({
        'success': True,
        'customer_id': customer.id,
        'customer_name': customer.name,
        'tier': loyalty.tier,
        'points_balance': loyalty.points_balance,
        'points_value': float(Decimal(loyalty.points_balance) * Decimal('0.05')),
        'lifetime_spend': float(loyalty.lifetime_spend)
    })


@login_required
@require_GET
def api_validate_coupon(request):
    code = request.GET.get('code', '').strip()
    subtotal = Decimal(request.GET.get('subtotal', '0'))
    res = POSPricingEngine.validate_and_apply_coupon(code, subtotal)
    return JsonResponse({
        'valid': res['valid'],
        'message': res['message'],
        'discount': float(res['discount']),
        'code': code
    })


@login_required
@require_POST
def api_process_order(request):
    try:
        payload = json.loads(request.body)
        session_id = payload.get('session_id')
        session = get_object_or_404(POSSession, pk=session_id)

        items_data = payload.get('items', [])
        if not items_data:
            return JsonResponse({'success': False, 'message': 'Cart is empty.'}, status=400)

        payments_data = payload.get('payments', [])
        if not payments_data:
            return JsonResponse({'success': False, 'message': 'No payment entries provided.'}, status=400)

        customer_id = payload.get('customer_id')
        customer = Customer.objects.filter(pk=customer_id).first() if customer_id else None

        coupon_code = payload.get('coupon_code', '').strip()
        loyalty_points = int(payload.get('loyalty_points', 0))
        notes = payload.get('notes', '')

        order = POSOrderProcessor.process_checkout(
            session=session,
            cashier=request.user,
            items_data=items_data,
            payments_data=payments_data,
            customer=customer,
            coupon_code=coupon_code if coupon_code else None,
            loyalty_points_to_redeem=loyalty_points,
            notes=notes
        )

        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number,
            'grand_total': float(order.grand_total),
            'paid_amount': float(order.paid_amount),
            'change_returned': float(order.change_returned),
            'loyalty_points_earned': order.loyalty_points_earned,
            'receipt_url': f"/pos/order/{order.id}/receipt/"
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
