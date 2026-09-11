from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Customer, Quotation, QuotationItem, SalesOrder, SalesOrderItem, Invoice, InvoiceItem, Payment, CreditNote
from .forms import CustomerForm, QuotationForm, SalesOrderForm, PaymentForm
from inventory.services import StockService
from workflows.engine import WorkflowEngine
from audit.middleware import log_audit_event

@login_required
def sales_dashboard(request):
    total_sales = Invoice.objects.filter(status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    outstanding_invoices = Invoice.objects.filter(status__in=['ISSUED', 'PARTIAL', 'OVERDUE']).aggregate(Sum('balance_due'))['balance_due__sum'] or 0
    active_orders = SalesOrder.objects.filter(status__in=['CONFIRMED', 'SHIPPED']).count()
    customers_count = Customer.objects.filter(is_active=True).count()

    recent_orders = SalesOrder.objects.select_related('customer', 'created_by').order_by('-order_date')[:6]
    recent_invoices = Invoice.objects.select_related('customer').order_by('-invoice_date')[:6]

    return render(request, 'sales/dashboard.html', {
        'total_sales': total_sales,
        'outstanding_invoices': outstanding_invoices,
        'active_orders': active_orders,
        'customers_count': customers_count,
        'recent_orders': recent_orders,
        'recent_invoices': recent_invoices,
    })

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    search = request.GET.get('q')
    if search:
        customers = customers.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(company_name__icontains=search) | Q(email__icontains=search))

    paginator = Paginator(customers, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'sales/customer_list.html', {'page_obj': page_obj})

@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cust = form.save()
        log_audit_event(request.user, 'CREATE', 'Customer', cust.id, str(cust), request=request)
        messages.success(request, f'Customer {cust} created successfully!')
        return redirect('sales:customer_list')
    return render(request, 'sales/customer_form.html', {'form': form, 'title': 'Add New Customer'})

@login_required
def quotation_list(request):
    quotes = Quotation.objects.select_related('customer', 'created_by').all()
    paginator = Paginator(quotes, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'sales/quotation_list.html', {'page_obj': page_obj})

@login_required
def quotation_detail(request, pk):
    quote = get_object_or_404(Quotation.objects.select_related('customer', 'created_by'), pk=pk)
    items = quote.items.select_related('product').all()

    if request.method == 'POST' and 'convert_to_order' in request.POST:
        so = SalesOrder.objects.create(
            order_number=f"SO-2026-{SalesOrder.objects.count() + 1:04d}",
            quotation=quote,
            customer=quote.customer,
            order_date=quote.date,
            subtotal=quote.subtotal,
            discount_amount=quote.discount_amount,
            tax_amount=quote.tax_amount,
            total_amount=quote.total_amount,
            created_by=request.user,
            status='CONFIRMED'
        )
        for itm in items:
            SalesOrderItem.objects.create(
                order=so,
                product=itm.product,
                quantity=itm.quantity,
                unit_price=itm.unit_price,
                discount_percent=itm.discount_percent,
                total=itm.total
            )
        quote.status = 'ACCEPTED'
        quote.save(update_fields=['status'])
        log_audit_event(request.user, 'CREATE', 'SalesOrder', so.id, str(so), request=request, description=f"Generated from Quote #{quote.quote_number}")
        messages.success(request, f'Sales Order #{so.order_number} created from quotation!')
        return redirect('sales:order_detail', pk=so.id)

    return render(request, 'sales/quotation_detail.html', {'quote': quote, 'items': items})

@login_required
def order_list(request):
    orders = SalesOrder.objects.select_related('customer', 'created_by').all()
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'sales/order_list.html', {
        'page_obj': page_obj,
        'statuses': SalesOrder.STATUS_CHOICES,
        'selected_status': status_filter,
    })

@login_required
def order_detail(request, pk):
    order = get_object_or_404(SalesOrder.objects.select_related('customer', 'created_by'), pk=pk)
    items = order.items.select_related('product').all()
    invoices = order.invoices.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'fulfill_delivery':
            # Deduct stock for all items
            for itm in items:
                try:
                    StockService.record_movement(
                        product=itm.product,
                        movement_type='SALES_DELIVERY',
                        quantity=itm.quantity,
                        unit_cost=itm.product.cost_price,
                        reference_number=f"SO-{order.order_number}",
                        user=request.user,
                        notes=f"Delivery fulfillment for {order.customer}"
                    )
                except ValueError as e:
                    messages.error(request, str(e))
                    return redirect('sales:order_detail', pk=pk)

            order.status = 'SHIPPED'
            order.save(update_fields=['status'])
            log_audit_event(request.user, 'UPDATE', 'SalesOrder', order.id, str(order), request=request, description="Fulfilled order & dispatched stock.")
            messages.success(request, f"Sales Order #{order.order_number} items dispatched and inventory deducted.")
            return redirect('sales:order_detail', pk=pk)

        elif action == 'generate_invoice':
            inv_num = f"INV-2026-{Invoice.objects.count() + 1:04d}"
            inv = Invoice.objects.create(
                invoice_number=inv_num,
                sales_order=order,
                customer=order.customer,
                invoice_date=order.order_date,
                due_date=order.order_date,
                status='ISSUED',
                subtotal=order.subtotal,
                tax_amount=order.tax_amount,
                total_amount=order.total_amount,
                paid_amount=Decimal('0.00'),
                balance_due=order.total_amount,
                created_by=request.user
            )
            for itm in items:
                InvoiceItem.objects.create(
                    invoice=inv,
                    product=itm.product,
                    quantity=itm.quantity,
                    unit_price=itm.unit_price,
                    tax_amount=itm.total * Decimal('0.10'),
                    total=itm.total
                )
            order.status = 'INVOICED'
            order.save(update_fields=['status'])
            log_audit_event(request.user, 'CREATE', 'Invoice', inv.id, str(inv), request=request, description=f"Generated invoice for Order #{order.order_number}")
            messages.success(request, f"Invoice #{inv_num} generated!")
            return redirect('sales:invoice_detail', pk=inv.id)

    return render(request, 'sales/order_detail.html', {'order': order, 'items': items, 'invoices': invoices})

@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('customer', 'created_by').all()
    status_filter = request.GET.get('status')
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    paginator = Paginator(invoices, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'sales/invoice_list.html', {'page_obj': page_obj, 'statuses': Invoice.STATUS_CHOICES, 'selected_status': status_filter})

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('customer', 'created_by'), pk=pk)
    items = invoice.items.select_related('product').all()
    payments = invoice.payments.select_related('created_by').all()
    pay_form = PaymentForm(request.POST or None, initial={'amount': invoice.balance_due, 'payment_number': f"PAY-{Payment.objects.count() + 1:04d}"})

    if request.method == 'POST' and 'record_payment' in request.POST:
        if pay_form.is_valid():
            pay = pay_form.save(commit=False)
            pay.invoice = invoice
            pay.customer = invoice.customer
            pay.created_by = request.user
            pay.save()

            invoice.paid_amount += pay.amount
            invoice.update_balance()

            log_audit_event(request.user, 'CREATE', 'Payment', pay.id, str(pay), request=request, description=f"Recorded payment ${pay.amount} on INV #{invoice.invoice_number}")
            messages.success(request, f"Payment of ${pay.amount:,.2f} recorded!")
            return redirect('sales:invoice_detail', pk=pk)

    return render(request, 'sales/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'payments': payments,
        'pay_form': pay_form,
    })
