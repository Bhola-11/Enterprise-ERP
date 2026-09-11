from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q

from .models import (
    RoomType, HotelRoom, GuestProfile, RoomReservation,
    GuestFolioInvoice, FolioChargeLine, HousekeepingTask
)
from .forms import (
    GuestProfileForm, RoomReservationForm, AddFolioChargeForm,
    HousekeepingTaskForm
)
from .services import FrontDeskService, FolioBillingService


@login_required
def hospitality_dashboard(request):
    total_rooms = HotelRoom.objects.count()
    occupied_rooms = HotelRoom.objects.filter(status='OCCUPIED').count()
    available_rooms = HotelRoom.objects.filter(status='AVAILABLE').count()
    dirty_rooms = HotelRoom.objects.filter(status='CLEANING').count()
    maintenance_rooms = HotelRoom.objects.filter(status='MAINTENANCE').count()

    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    today = timezone.now().date()
    arrivals_today = RoomReservation.objects.filter(check_in_date=today, status='CONFIRMED').count()
    departures_today = RoomReservation.objects.filter(check_out_date=today, status='CHECKED_IN').count()

    in_house_reservations = RoomReservation.objects.filter(status='CHECKED_IN').select_related('guest', 'room', 'room_type')
    recent_reservations = RoomReservation.objects.select_related('guest', 'room', 'room_type').order_by('-created_at')[:10]

    context = {
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'available_rooms': available_rooms,
        'dirty_rooms': dirty_rooms,
        'maintenance_rooms': maintenance_rooms,
        'occupancy_rate': round(occupancy_rate, 1),
        'arrivals_today': arrivals_today,
        'departures_today': departures_today,
        'in_house_reservations': in_house_reservations,
        'recent_reservations': recent_reservations,
        'page_title': 'Hospitality & Hotel PMS Hub',
    }
    return render(request, 'hospitality_pms/dashboard.html', context)


@login_required
def room_matrix(request):
    rooms = HotelRoom.objects.select_related('room_type').order_by('floor', 'room_number')
    room_types = RoomType.objects.all()

    return render(request, 'hospitality_pms/room_matrix.html', {
        'rooms': rooms,
        'room_types': room_types,
        'page_title': 'Live Room Rack & Housekeeping Matrix'
    })


@login_required
def reservation_list(request):
    status = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()

    reservations = RoomReservation.objects.select_related('guest', 'room', 'room_type').order_by('-check_in_date')
    if status:
        reservations = reservations.filter(status=status)
    if query:
        reservations = reservations.filter(
            Q(confirmation_code__icontains=query) |
            Q(guest__first_name__icontains=query) |
            Q(guest__last_name__icontains=query)
        )

    return render(request, 'hospitality_pms/reservation_list.html', {
        'reservations': reservations[:100],
        'selected_status': status,
        'query': query,
        'page_title': 'Hotel Reservations & Bookings'
    })


@login_required
def reservation_create(request):
    if request.method == 'POST':
        form = RoomReservationForm(request.POST)
        if form.is_valid():
            res = form.save(commit=False)
            res.confirmation_code = f"RES-{timezone.now().strftime('%y%m%d%H%M')}"
            nights = max(1, (res.check_out_date - res.check_in_date).days)
            res.total_room_charge = res.nightly_rate * nights
            res.status = 'CONFIRMED'
            res.save()
            messages.success(request, f"Reservation {res.confirmation_code} created for {res.guest.full_name}.")
            return redirect('hospitality_pms:reservation_detail', pk=res.id)
    else:
        first_rt = RoomType.objects.first()
        rate = first_rt.base_nightly_rate if first_rt else Decimal('150.00')
        form = RoomReservationForm(initial={
            'check_in_date': timezone.now().date(),
            'check_out_date': timezone.now().date() + timezone.timedelta(days=2),
            'nightly_rate': rate,
            'deposit_paid': Decimal('0.00'),
        })

    return render(request, 'hospitality_pms/reservation_form.html', {'form': form, 'page_title': 'New Guest Room Reservation'})


@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(
        RoomReservation.objects.select_related('guest', 'room', 'room_type'),
        pk=pk
    )
    folio = getattr(reservation, 'folio', None)
    charge_form = AddFolioChargeForm()

    return render(request, 'hospitality_pms/reservation_detail.html', {
        'reservation': reservation,
        'folio': folio,
        'charge_form': charge_form,
        'page_title': f'Booking #{reservation.confirmation_code}'
    })


@login_required
def check_in_guest(request, pk):
    reservation = get_object_or_404(RoomReservation, pk=pk)
    # Check if a room is assigned or pick available
    if not reservation.room:
        available_room = HotelRoom.objects.filter(room_type=reservation.room_type, status='AVAILABLE').first()
        if not available_room:
            available_room = HotelRoom.objects.filter(status='AVAILABLE').first()
        if available_room:
            reservation.room = available_room

    try:
        FrontDeskService.process_check_in(reservation)
        messages.success(request, f"Guest {reservation.guest.full_name} checked into Room {reservation.room.room_number}.")
    except Exception as e:
        messages.error(request, f"Check-in failed: {str(e)}")

    return redirect('hospitality_pms:reservation_detail', pk=reservation.id)


@login_required
def check_out_guest(request, pk):
    reservation = get_object_or_404(RoomReservation, pk=pk)
    try:
        FrontDeskService.process_check_out(reservation, user=request.user)
        messages.success(request, f"Guest {reservation.guest.full_name} checked out. Folio settled & posted to GL.")
    except Exception as e:
        messages.error(request, f"Check-out failed: {str(e)}")

    return redirect('hospitality_pms:reservation_detail', pk=reservation.id)


@login_required
def add_folio_charge(request, pk):
    reservation = get_object_or_404(RoomReservation, pk=pk)
    folio = get_object_or_404(GuestFolioInvoice, reservation=reservation)
    if request.method == 'POST':
        form = AddFolioChargeForm(request.POST)
        if form.is_valid():
            FolioBillingService.post_charge(
                folio=folio,
                charge_type=form.cleaned_data['charge_type'],
                description=form.cleaned_data['description'],
                amount=form.cleaned_data['amount']
            )
            messages.success(request, "Incidental charge added to guest folio.")
    return redirect('hospitality_pms:reservation_detail', pk=reservation.id)


@login_required
def housekeeping_board(request):
    tasks = HousekeepingTask.objects.select_related('room', 'room__room_type').order_by('-created_at')
    dirty_rooms = HotelRoom.objects.filter(status__in=['CLEANING', 'MAINTENANCE']).select_related('room_type')

    return render(request, 'hospitality_pms/housekeeping_board.html', {
        'tasks': tasks[:50],
        'dirty_rooms': dirty_rooms,
        'page_title': 'Housekeeping Operations & Inspection Board'
    })
