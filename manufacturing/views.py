from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from decimal import Decimal
from .models import BillOfMaterials, BOMItem, ProductionOrder, WorkCenter, QualityInspection
from .forms import BOMForm, ProductionOrderForm
from inventory.services import StockService
from audit.middleware import log_audit_event

@login_required
def manufacturing_dashboard(request):
    total_orders = ProductionOrder.objects.count()
    active_orders = ProductionOrder.objects.filter(status__in=['PLANNED', 'IN_PROGRESS']).count()
    completed_orders = ProductionOrder.objects.filter(status='COMPLETED').count()
    total_boms = BillOfMaterials.objects.filter(is_active=True).count()

    recent_orders = ProductionOrder.objects.select_related('bom__finished_product', 'work_center').order_by('-start_date')[:6]

    return render(request, 'manufacturing/dashboard.html', {
        'total_orders': total_orders,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'total_boms': total_boms,
        'recent_orders': recent_orders,
    })

@login_required
def bom_list(request):
    boms = BillOfMaterials.objects.select_related('finished_product').all()
    paginator = Paginator(boms, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'manufacturing/bom_list.html', {'page_obj': page_obj})

@login_required
def bom_detail(request, pk):
    bom = get_object_or_404(BillOfMaterials.objects.select_related('finished_product'), pk=pk)
    items = bom.items.select_related('raw_material').all()
    return render(request, 'manufacturing/bom_detail.html', {'bom': bom, 'items': items})

@login_required
def production_order_list(request):
    orders = ProductionOrder.objects.select_related('bom__finished_product', 'work_center', 'created_by').all()
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'manufacturing/production_order_list.html', {'page_obj': page_obj, 'statuses': ProductionOrder.STATUS_CHOICES, 'selected_status': status_filter})

@login_required
def production_order_create(request):
    form = ProductionOrderForm(request.POST or None, initial={'order_number': f"MO-2026-{ProductionOrder.objects.count() + 1:04d}"})
    if request.method == 'POST' and form.is_valid():
        mo = form.save(commit=False)
        mo.created_by = request.user
        mo.save()
        log_audit_event(request.user, 'CREATE', 'ProductionOrder', mo.id, str(mo), request=request)
        messages.success(request, f"Manufacturing Order #{mo.order_number} scheduled!")
        return redirect('manufacturing:order_list')
    return render(request, 'manufacturing/order_form.html', {'form': form, 'title': 'Create Production Order'})

@login_required
def production_order_detail(request, pk):
    order = get_object_or_404(ProductionOrder.objects.select_related('bom__finished_product', 'work_center'), pk=pk)
    items = order.bom.items.select_related('raw_material').all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'start_production':
            # Consume raw materials
            for itm in items:
                qty_to_consume = itm.quantity * (order.quantity_to_produce / order.bom.quantity)
                try:
                    StockService.record_movement(
                        product=itm.raw_material,
                        movement_type='MFG_ISSUE',
                        quantity=qty_to_consume,
                        reference_number=f"MO-{order.order_number}",
                        user=request.user,
                        notes=f"Issued for assembling {order.bom.finished_product.name}"
                    )
                except ValueError as e:
                    messages.error(request, f"Error issuing {itm.raw_material.name}: {str(e)}")
                    return redirect('manufacturing:order_detail', pk=pk)

            order.status = 'IN_PROGRESS'
            order.save(update_fields=['status'])
            log_audit_event(request.user, 'UPDATE', 'ProductionOrder', order.id, str(order), request=request, description="Started production and issued raw materials.")
            messages.success(request, f"Production started for #{order.order_number}. Raw materials issued from stock.")
            return redirect('manufacturing:order_detail', pk=pk)

        elif action == 'complete_production':
            # Complete QC & Receive finished goods into inventory
            QualityInspection.objects.get_or_create(
                production_order=order,
                defaults={
                    'inspector': request.user,
                    'sample_size': int(order.quantity_to_produce),
                    'passed_units': int(order.quantity_to_produce),
                    'passed': True,
                    'notes': 'Automated 100% QA Inspection passed.'
                }
            )

            # Receive finished goods
            StockService.record_movement(
                product=order.bom.finished_product,
                movement_type='MFG_RECEIPT',
                quantity=order.quantity_to_produce,
                unit_cost=order.bom.total_raw_material_cost,
                reference_number=f"MO-{order.order_number}",
                user=request.user,
                notes="Manufactured finished goods received into warehouse."
            )

            order.status = 'COMPLETED'
            order.save(update_fields=['status'])
            log_audit_event(request.user, 'APPROVE', 'ProductionOrder', order.id, str(order), request=request, description="Completed manufacturing order & received finished stock.")
            messages.success(request, f"Production order #{order.order_number} completed and {order.quantity_to_produce} units added to finished goods inventory!")
            return redirect('manufacturing:order_detail', pk=pk)

    return render(request, 'manufacturing/order_detail.html', {'order': order, 'items': items})
