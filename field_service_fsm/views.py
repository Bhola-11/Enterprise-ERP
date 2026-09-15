import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import (
    ServiceTerritory, ServiceTechnician, WorkOrder, PartConsumption, CustomerSignoff
)
from .forms import WorkOrderCreateForm, PartConsumptionForm, CustomerSignoffForm
from .services import DispatchSchedulingEngine, InventoryConsumptionEngine, SLATrackerService

@login_required
def dashboard_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    work_orders = WorkOrder.objects.filter(organization=org) if org else WorkOrder.objects.all()

    total_orders = work_orders.count()
    active_orders = work_orders.filter(status__in=['DISPATCHED', 'EN_ROUTE', 'ON_SITE', 'WORK_IN_PROGRESS']).count()
    completed_orders = work_orders.filter(status='COMPLETED').count()
    emergency_orders = work_orders.filter(priority='CRITICAL_EMERGENCY').count()

    technicians = ServiceTechnician.objects.filter(organization=org) if org else ServiceTechnician.objects.all()
    available_techs = technicians.filter(is_available=True).count()

    recent_orders = work_orders.order_by('-created_at')[:6]

    context = {
        'total_orders': total_orders,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'emergency_orders': emergency_orders,
        'total_techs': technicians.count(),
        'available_techs': available_techs,
        'recent_orders': recent_orders,
    }
    return render(request, 'field_service_fsm/dashboard.html', context)


@login_required
def dispatch_board_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    technicians = ServiceTechnician.objects.filter(organization=org) if org else ServiceTechnician.objects.all()
    unassigned_wos = WorkOrder.objects.filter(status='UNASSIGNED')
    if org:
        unassigned_wos = unassigned_wos.filter(organization=org)

    if request.method == 'POST':
        wo_id = request.POST.get('work_order_id')
        tech_id = request.POST.get('technician_id')
        if wo_id and tech_id:
            wo = get_object_or_404(WorkOrder, id=wo_id)
            tech = get_object_or_404(ServiceTechnician, id=tech_id)
            DispatchSchedulingEngine.dispatch_work_order(wo, tech)
            messages.success(request, f"Work Order #{wo.work_order_number} successfully dispatched to {tech.user.get_full_name() or tech.user.username}!")
            return redirect('field_service_fsm:dispatch_board')

    context = {
        'technicians': technicians,
        'unassigned_wos': unassigned_wos,
    }
    return render(request, 'field_service_fsm/dispatch_board.html', context)


@login_required
def work_order_list_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    work_orders = WorkOrder.objects.filter(organization=org) if org else WorkOrder.objects.all()
    context = {'work_orders': work_orders}
    return render(request, 'field_service_fsm/work_order_list.html', context)


@login_required
def work_order_create_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None

    if request.method == 'POST':
        form = WorkOrderCreateForm(request.POST)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.organization = org if org else (wo.customer.organization if wo.customer else None)
            wo.work_order_number = f"WO-{timezone.now().year}-{uuid.uuid4().hex[:6].upper()}"
            wo.save()
            messages.success(request, f"Work order {wo.work_order_number} logged successfully!")
            return redirect('field_service_fsm:work_order_list')
    else:
        now = timezone.now()
        form = WorkOrderCreateForm(initial={
            'scheduled_start': now,
            'scheduled_end': now + timezone.timedelta(hours=3),
            'sla_deadline': now + timezone.timedelta(hours=4)
        })

    context = {'form': form}
    return render(request, 'field_service_fsm/work_order_form.html', context)


@login_required
def work_order_detail_view(request, pk):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    wo = get_object_or_404(WorkOrder, pk=pk)
    sla_info = SLATrackerService.check_sla_compliance(wo)
    parts = wo.consumed_parts.all()

    context = {
        'wo': wo,
        'sla_info': sla_info,
        'parts': parts,
    }
    return render(request, 'field_service_fsm/work_order_detail.html', context)


@login_required
def consume_parts_view(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk)

    if request.method == 'POST':
        form = PartConsumptionForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            consumption = InventoryConsumptionEngine.record_part_consumption(wo, product, quantity)
            messages.success(request, f"Deducted {quantity} units of {product.name} from warehouse inventory.")
            return redirect('field_service_fsm:work_order_detail', pk=wo.id)
    else:
        form = PartConsumptionForm()

    context = {'wo': wo, 'form': form}
    return render(request, 'field_service_fsm/technician_portal.html', context)


@login_required
def customer_signoff_view(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk)

    if request.method == 'POST':
        form = CustomerSignoffForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['signatory_name']
            rating = form.cleaned_data['satisfaction_rating']
            notes = form.cleaned_data['feedback_notes']
            signoff = SLATrackerService.complete_with_signoff(wo, name, rating, notes)
            messages.success(request, f"Work Order #{wo.work_order_number} completed and digitally signed by {name} ({rating} Stars)!")
            return redirect('field_service_fsm:work_order_detail', pk=wo.id)
    else:
        form = CustomerSignoffForm()

    context = {'wo': wo, 'form': form}
    return render(request, 'field_service_fsm/customer_signoff.html', context)
