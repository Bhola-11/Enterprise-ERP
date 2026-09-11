from django.contrib import admin
from .models import (
    RoomType, HotelRoom, GuestProfile, RoomReservation,
    GuestFolioInvoice, FolioChargeLine, HousekeepingTask
)

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'base_occupancy', 'base_nightly_rate')

@admin.register(HotelRoom)
class HotelRoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'floor', 'status')
    list_filter = ('status', 'floor', 'room_type')

@admin.register(GuestProfile)
class GuestProfileAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'vip_tier', 'nationality')
    search_fields = ('first_name', 'last_name', 'email')

class FolioChargeLineInline(admin.TabularInline):
    model = FolioChargeLine
    extra = 1

@admin.register(GuestFolioInvoice)
class GuestFolioInvoiceAdmin(admin.ModelAdmin):
    list_display = ('folio_number', 'guest', 'total_amount', 'paid_amount', 'balance_amount', 'status')
    list_filter = ('status',)
    inlines = [FolioChargeLineInline]

@admin.register(RoomReservation)
class RoomReservationAdmin(admin.ModelAdmin):
    list_display = ('confirmation_code', 'guest', 'room', 'room_type', 'check_in_date', 'check_out_date', 'status')
    list_filter = ('status', 'booking_source')

@admin.register(HousekeepingTask)
class HousekeepingTaskAdmin(admin.ModelAdmin):
    list_display = ('room', 'task_type', 'status', 'assigned_housekeeper', 'created_at')
    list_filter = ('status', 'task_type')
