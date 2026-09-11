from django.contrib import admin
from .models import Driver, Vehicle, FuelLog, TripRecord

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('employee', 'license_number', 'license_expiry', 'is_available')

class FuelLogInline(admin.TabularInline):
    model = FuelLog
    extra = 1

class TripRecordInline(admin.TabularInline):
    model = TripRecord
    extra = 1

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'make', 'model', 'year', 'fuel_type', 'current_odometer_km', 'status', 'assigned_driver')
    list_filter = ('status', 'fuel_type')
    search_fields = ('plate_number', 'make', 'model', 'vin')
    inlines = [FuelLogInline, TripRecordInline]

@admin.register(FuelLog)
class FuelLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date', 'liters', 'cost_per_liter', 'total_cost', 'odometer_km')

@admin.register(TripRecord)
class TripRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'driver', 'date', 'start_location', 'end_location', 'distance_km')
