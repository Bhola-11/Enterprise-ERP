import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from accounting.models import JournalEntry

class RoomType(models.Model):
    code = models.CharField(max_length=30, unique=True) # e.g. LUX-SUITE
    name = models.CharField(max_length=150) # Luxury Ocean Suite
    base_occupancy = models.PositiveIntegerField(default=2)
    max_occupancy = models.PositiveIntegerField(default=4)
    base_nightly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('200.00'))
    description = models.TextField(blank=True)
    amenities = models.TextField(blank=True) # King Bed, Jacuzzi, Balcony, Sea View, MiniBar

    def __str__(self):
        return f"{self.name} (${self.base_nightly_rate}/night)"


class HotelRoom(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available / Vacant Clean'),
        ('OCCUPIED', 'Occupied / In-House'),
        ('RESERVED', 'Reserved for Arrival'),
        ('CLEANING', 'Housekeeping / Dirty'),
        ('MAINTENANCE', 'Out of Order / Maintenance'),
    ]
    room_number = models.CharField(max_length=30, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name='rooms')
    floor = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    keycard_lock_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.code})"


class GuestProfile(models.Model):
    VIP_TIERS = [
        ('STANDARD', 'Standard Guest'),
        ('SILVER', 'Silver Elite'),
        ('GOLD', 'Gold Preferred'),
        ('PLATINUM', 'Platinum Executive VIP'),
        ('CELEBRITY', 'VVIP Ambassador'),
    ]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50)
    id_passport_number = models.CharField(max_length=50, blank=True)
    nationality = models.CharField(max_length=100, default='United States')
    vip_tier = models.CharField(max_length=20, choices=VIP_TIERS, default='STANDARD')
    special_preferences = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name} ({self.vip_tier})"


class RoomReservation(models.Model):
    SOURCE_CHOICES = [
        ('DIRECT_DESK', 'Front Desk Walk-in / Phone'),
        ('WEBSITE', 'Direct Website Booking Engine'),
        ('BOOKING_COM', 'Booking.com OTA Channel'),
        ('EXPEDIA', 'Expedia Partner Network'),
        ('AGODA', 'Agoda Global'),
        ('CORPORATE', 'Corporate Travel Contract'),
    ]
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed Booking'),
        ('CHECKED_IN', 'Checked In (In-House)'),
        ('CHECKED_OUT', 'Checked Out (Departed)'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]
    confirmation_code = models.CharField(max_length=50, unique=True)
    guest = models.ForeignKey(GuestProfile, on_delete=models.PROTECT, related_name='reservations')
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name='reservations')
    room = models.ForeignKey(HotelRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.PositiveIntegerField(default=1)
    nightly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    total_room_charge = models.DecimalField(max_digits=12, decimal_places=2)
    deposit_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    booking_source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='DIRECT_DESK')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    actual_check_in_time = models.DateTimeField(null=True, blank=True)
    actual_check_out_time = models.DateTimeField(null=True, blank=True)
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_nights(self):
        from datetime import date
        cin = self.check_in_date
        cout = self.check_out_date
        if isinstance(cin, str):
            cin = date.fromisoformat(cin)
        if isinstance(cout, str):
            cout = date.fromisoformat(cout)
        diff = (cout - cin).days
        return max(1, diff)

    def __str__(self):
        return f"{self.confirmation_code}: {self.guest.full_name} ({self.check_in_date} -> {self.check_out_date})"


class GuestFolioInvoice(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open Folio (In-House)'),
        ('SETTLED', 'Settled & Paid In Full'),
        ('VOID', 'Voided / Cancelled'),
    ]
    folio_number = models.CharField(max_length=50, unique=True)
    reservation = models.OneToOneField(RoomReservation, on_delete=models.CASCADE, related_name='folio')
    guest = models.ForeignKey(GuestProfile, on_delete=models.CASCADE, related_name='folios')
    total_room_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_incidentals = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"FOLIO-{self.folio_number} (${self.total_amount})"


class FolioChargeLine(models.Model):
    CHARGE_TYPES = [
        ('ROOM_NIGHT', 'Room Accommodation Charge'),
        ('RESTAURANT', 'In-Room Dining / Restaurant'),
        ('MINIBAR', 'Minibar Refreshments'),
        ('SPA_WELLNESS', 'Spa, Massage & Wellness'),
        ('LAUNDRY', 'Valet Laundry Service'),
        ('TRANSPORT', 'Airport Limousine Transfer'),
        ('RESORT_FEE', 'Daily Resort / Amenity Fee'),
    ]
    folio = models.ForeignKey(GuestFolioInvoice, on_delete=models.CASCADE, related_name='charge_lines')
    charge_type = models.CharField(max_length=30, choices=CHARGE_TYPES, default='ROOM_NIGHT')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    charged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_charge_type_display()}: ${self.amount}"


class HousekeepingTask(models.Model):
    TASK_TYPES = [
        ('CHECKOUT_DEEP_CLEAN', 'Full Departure Deep Cleaning'),
        ('STAY_OVER_CLEAN', 'Stay-Over Daily Refresh'),
        ('TURNDOWN', 'Evening Turndown Service'),
        ('LINEN_CHANGE', 'Complete Linen & Towel Swap'),
        ('SANITIZE', 'Full Sanitization Inspection'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Assignment'),
        ('IN_PROGRESS', 'Cleaning In Progress'),
        ('INSPECTED_CLEAN', 'Inspected Clean / Ready for Guest'),
        ('NEEDS_REWORK', 'Failed Inspection / Needs Rework'),
    ]
    room = models.ForeignKey(HotelRoom, on_delete=models.CASCADE, related_name='housekeeping_tasks')
    task_type = models.CharField(max_length=30, choices=TASK_TYPES, default='CHECKOUT_DEEP_CLEAN')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    assigned_housekeeper = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Room {self.room.room_number} - {self.get_task_type_display()} ({self.get_status_display()})"
