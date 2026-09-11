from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q

from .models import (
    SubcontractorVendor, SubcontractOrder, SubcontractMaterialDispatch,
    SubcontractGoodsReceipt
)
from .forms import (
    SubcontractorVendorForm, SubcontractOrderForm, SubcontractGoodsReceiptForm
)
from .services import SubcontractExecutionService


@login_required
def subcontract_dashboard(request):
    total_vendors = SubcontractorVendor.objects.count()
    active_orders = SubcontractOrder.objects.filter(status__in=['DRAFT', 'MATERIALS_DISPATCHED', 'IN_PROCESSING', 'PARTIALLY_RECEIVED']).count()
    completed_orders = SubcontractOrder.objects.filter(status='COMPLETED').count()
    total_spend = SubcontractOrder.objects.filter(status='COMPLETED').aggregate(s=Sum('total_service_cost'))['s'] or Decimal('0.00')

    recent_orders = SubcontractOrder.objects.select_related('subcontractor', 'finished_product').order_by('-created_at')[:8]
    vendors = SubcontractorVendor.objects.filter(is_active=True)

    context = {
        'total_vendors': total_vendors,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'total_spend': total_spend,
        'recent_orders': recent_orders,
        'vendors': vendors,
        'page_title': 'Subcontracting & Job Work Operations Hub',
    }
    return render(request, 'subcontracting/dashboard.html', context)


@login_required
def vendor_list(request):
    vendors = SubcontractorVendor.objects.annotate(orders_count=Count('orders')).all()
    return render(request, 'subcontracting/vendor_list.html', {
        'vendors': vendors,
        'page_title': 'Subcontractors & Job Work Partners'
    })


@login_required
def vendor_create(request):
    if request.method == 'POST':
        form = SubcontractorVendorForm(request.POST)
        if form.is_valid():
            v = form.save()
            messages.success(request, f"Vendor {v.name} ({v.code}) created.")
            return redirect('subcontracting:vendor_list')
    else:
        form = SubcontractorVendorForm()
    return render(request, 'subcontracting/vendor_form.html', {'form': form, 'page_title': 'Register Job Work Partner'})


@login_required
def order_list(request):
    status = request.GET.get('status', '')
    orders = SubcontractOrder.objects.select_related('subcontractor', 'finished_product').order_by('-order_date')
    if status:
        orders = orders.filter(status=status)

    return render(request, 'subcontracting/order_list.html', {
        'orders': orders[:100],
        'selected_status': status,
        'page_title': 'Subcontract Work Orders'
    })


@login_required
def order_create(request):
    if request.method == 'POST':
        form = SubcontractOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.order_number = f"SCO-{timezone.now().strftime('%y%m%d%H%M')}"
            order.total_service_cost = order.planned_quantity * order.unit_processing_rate
            order.status = 'DRAFT'
            order.created_by = request.user
            order.save()
            messages.success(request, f"Subcontract Order #{order.order_number} created.")
            return redirect('subcontracting:order_detail', pk=order.id)
    else:
        form = SubcontractOrderForm(initial={
            'order_date': timezone.now().date(),
            'expected_delivery_date': timezone.now().date() + timezone.timedelta(days=14),
            'planned_quantity': Decimal('100.00'),
            'unit_processing_rate': Decimal('15.00'),
        })

    return render(request, 'subcontracting/order_form.html', {'form': form, 'page_title': 'Create Subcontract Work Order'})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(SubcontractOrder.objects.select_related('subcontractor', 'finished_product'), pk=pk)
    dispatches = order.dispatches.select_related('raw_material').all()
    receipts = order.receipts.all()

    if request.method == 'POST':
        receipt_form = SubcontractGoodsReceiptForm(request.POST)
        if receipt_form.is_valid():
            qty = receipt_form.cleaned_data['quantity_received']
            rej = receipt_form.cleaned_data['quantity_rejected']
            scrap = receipt_form.cleaned_data['scrap_material_reported']
            ref = receipt_form.cleaned_data['vendor_delivery_note_ref']
            sgrn = SubcontractExecutionService.receive_finished_goods(order, qty, rej, scrap, ref, user=request.user)
            messages.success(request, f"Received {qty} units under SGRN #{sgrn.receipt_number}. Posted toll cost to GL.")
            return redirect('subcontracting:order_detail', pk=order.id)
    else:
        receipt_form = SubcontractGoodsReceiptForm(initial={'quantity_received': order.planned_quantity})

    return render(request, 'subcontracting/order_detail.html', {
        'order': order,
        'dispatches': dispatches,
        'receipts': receipts,
        'receipt_form': receipt_form,
        'page_title': f'Subcontract Order: {order.order_number}'
    })
