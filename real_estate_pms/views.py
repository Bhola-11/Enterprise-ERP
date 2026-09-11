from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q

from .models import (
    PropertyComplex, PropertyUnit, PropertyTenant, LeaseAgreement,
    TenantRentInvoice, MaintenanceWorkOrder
)
from .forms import (
    PropertyComplexForm, PropertyUnitForm, LeaseAgreementForm,
    MaintenanceWorkOrderForm
)
from .services import LeaseManagementService, RentCollectionService


@login_required
def pms_dashboard(request):
    total_properties = PropertyComplex.objects.count()
    total_units = PropertyUnit.objects.count()
    occupied_units = PropertyUnit.objects.filter(occupancy_status='LEASED').count()
    occupancy_pct = (occupied_units / total_units * 100) if total_units > 0 else 0
    
    active_leases = LeaseAgreement.objects.filter(status='ACTIVE').count()
    total_rent_collected = TenantRentInvoice.objects.aggregate(s=Sum('paid_amount'))['s'] or Decimal('0.00')
    total_rent_outstanding = TenantRentInvoice.objects.filter(status__in=['PENDING', 'PARTIAL', 'OVERDUE']).aggregate(s=Sum('balance_amount'))['s'] or Decimal('0.00')

    open_work_orders = MaintenanceWorkOrder.objects.filter(status__in=['REPORTED', 'ASSIGNED', 'IN_PROGRESS']).count()
    recent_leases = LeaseAgreement.objects.select_related('unit', 'unit__complex', 'tenant').order_by('-created_at')[:8]

    context = {
        'total_properties': total_properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'occupancy_pct': round(occupancy_pct, 1),
        'active_leases': active_leases,
        'total_rent_collected': total_rent_collected,
        'total_rent_outstanding': total_rent_outstanding,
        'open_work_orders': open_work_orders,
        'recent_leases': recent_leases,
        'page_title': 'Real Estate & Commercial PMS Hub',
    }
    return render(request, 'real_estate_pms/dashboard.html', context)


@login_required
def property_list(request):
    complexes = PropertyComplex.objects.annotate(
        unit_count=Count('units'),
        active_leases_count=Count('units__leases', filter=Q(units__leases__status='ACTIVE'))
    ).order_by('name')

    return render(request, 'real_estate_pms/property_list.html', {
        'complexes': complexes,
        'page_title': 'Property Portfolios & Commercial Buildings'
    })


@login_required
def unit_list(request):
    status = request.GET.get('status', '')
    complex_id = request.GET.get('complex', '')

    units = PropertyUnit.objects.select_related('complex').order_by('complex', 'floor_number', 'unit_number')
    if status:
        units = units.filter(occupancy_status=status)
    if complex_id:
        units = units.filter(complex_id=complex_id)

    complexes = PropertyComplex.objects.all()

    return render(request, 'real_estate_pms/unit_list.html', {
        'units': units[:100],
        'complexes': complexes,
        'selected_status': status,
        'selected_complex': complex_id,
        'page_title': 'Property Units & Suite Directory'
    })


@login_required
def unit_create(request):
    if request.method == 'POST':
        form = PropertyUnitForm(request.POST)
        if form.is_valid():
            u = form.save()
            messages.success(request, f"Unit {u.unit_number} added to {u.complex.name}.")
            return redirect('real_estate_pms:unit_list')
    else:
        form = PropertyUnitForm()
    return render(request, 'real_estate_pms/unit_form.html', {'form': form, 'page_title': 'Add Property Unit / Suite'})


@login_required
def lease_list(request):
    status = request.GET.get('status', '')
    leases = LeaseAgreement.objects.select_related('unit', 'unit__complex', 'tenant').order_by('-start_date')
    if status:
        leases = leases.filter(status=status)

    return render(request, 'real_estate_pms/lease_list.html', {
        'leases': leases[:100],
        'selected_status': status,
        'page_title': 'Commercial & Residential Leases'
    })


@login_required
def lease_create(request):
    if request.method == 'POST':
        form = LeaseAgreementForm(request.POST)
        if form.is_valid():
            lease = form.save(commit=False)
            lease.lease_number = f"LSE-{timezone.now().strftime('%y%m%d%H%M')}"
            lease.status = 'ACTIVE'
            lease.save()

            # Mark unit as leased
            LeaseManagementService.activate_lease(lease)
            # Generate first month invoice
            LeaseManagementService.generate_monthly_rent_invoice(lease)

            messages.success(request, f"Lease #{lease.lease_number} executed successfully.")
            return redirect('real_estate_pms:lease_detail', pk=lease.id)
    else:
        form = LeaseAgreementForm(initial={
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timezone.timedelta(days=365),
            'annual_escalation_pct': Decimal('5.00'),
            'payment_due_day': 1,
        })

    return render(request, 'real_estate_pms/lease_form.html', {'form': form, 'page_title': 'Draft New Lease Agreement'})


@login_required
def lease_detail(request, pk):
    lease = get_object_or_404(
        LeaseAgreement.objects.select_related('unit', 'unit__complex', 'tenant'),
        pk=pk
    )
    invoices = lease.rent_invoices.order_by('-period_start')
    work_orders = lease.unit.work_orders.order_by('-created_at')

    return render(request, 'real_estate_pms/lease_detail.html', {
        'lease': lease,
        'invoices': invoices,
        'work_orders': work_orders,
        'page_title': f'Lease Overview: {lease.lease_number}'
    })


@login_required
def work_order_list(request):
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')

    work_orders = MaintenanceWorkOrder.objects.select_related('unit', 'unit__complex', 'tenant').order_by('-created_at')
    if category:
        work_orders = work_orders.filter(category=category)
    if status:
        work_orders = work_orders.filter(status=status)

    return render(request, 'real_estate_pms/work_order_list.html', {
        'work_orders': work_orders[:100],
        'selected_category': category,
        'selected_status': status,
        'page_title': 'Facility Maintenance & Work Orders'
    })


@login_required
def work_order_create(request):
    if request.method == 'POST':
        form = MaintenanceWorkOrderForm(request.POST)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.work_order_number = f"WO-{timezone.now().strftime('%y%m%d%H%M')}"
            wo.status = 'REPORTED'
            wo.save()
            messages.success(request, f"Work Order #{wo.work_order_number} logged.")
            return redirect('real_estate_pms:work_order_list')
    else:
        form = MaintenanceWorkOrderForm()
    return render(request, 'real_estate_pms/work_order_form.html', {'form': form, 'page_title': 'Log Maintenance Work Order'})


@login_required
def rent_roll_report(request):
    active_leases = LeaseAgreement.objects.filter(status='ACTIVE').select_related('unit', 'unit__complex', 'tenant')
    total_monthly_roll = active_leases.aggregate(s=Sum('monthly_rent'))['s'] or Decimal('0.00')
    total_cam_roll = active_leases.aggregate(s=Sum('cam_fee_monthly'))['s'] or Decimal('0.00')

    return render(request, 'real_estate_pms/rent_roll.html', {
        'leases': active_leases,
        'total_monthly_roll': total_monthly_roll,
        'total_cam_roll': total_cam_roll,
        'total_annual_revenue': (total_monthly_roll + total_cam_roll) * 12,
        'page_title': 'Commercial Rent Roll & Financial Audit'
    })
