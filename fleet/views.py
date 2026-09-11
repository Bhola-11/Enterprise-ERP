from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import Vehicle, Driver, FuelLog, TripRecord
from .forms import VehicleForm, FuelLogForm
from audit.middleware import log_audit_event

@login_required
def vehicle_list(request):
    vehicles = Vehicle.objects.select_related('assigned_driver__employee').all()
    status_filter = request.GET.get('status')
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)

    paginator = Paginator(vehicles, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    total_vehicles = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(status='ACTIVE').count()
    fuel_spend = FuelLog.objects.aggregate(Sum('total_cost'))['total_cost__sum'] or 0

    return render(request, 'fleet/vehicle_list.html', {
        'page_obj': page_obj,
        'statuses': Vehicle.STATUS_CHOICES,
        'selected_status': status_filter,
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'fuel_spend': fuel_spend,
    })

@login_required
def vehicle_create(request):
    form = VehicleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        veh = form.save()
        log_audit_event(request.user, 'CREATE', 'Vehicle', veh.id, str(veh), request=request)
        messages.success(request, f"Vehicle '{veh.plate_number}' added to fleet!")
        return redirect('fleet:list')
    return render(request, 'fleet/vehicle_form.html', {'form': form, 'title': 'Add Fleet Vehicle'})

@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle.objects.select_related('assigned_driver__employee'), pk=pk)
    fuel_logs = vehicle.fuel_logs.all()[:10]
    trips = vehicle.trips.select_related('driver__employee').all()[:10]
    return render(request, 'fleet/vehicle_detail.html', {'vehicle': vehicle, 'fuel_logs': fuel_logs, 'trips': trips})

@login_required
def fuel_log_create(request):
    form = FuelLogForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        f = form.save()
        log_audit_event(request.user, 'CREATE', 'FuelLog', f.id, str(f), request=request)
        messages.success(request, f"Fuel log recorded for {f.vehicle.plate_number}!")
        return redirect('fleet:detail', pk=f.vehicle.id)
    return render(request, 'fleet/fuel_log_form.html', {'form': form, 'title': 'Log Fuel Expense'})
