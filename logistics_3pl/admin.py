from django.contrib import admin
from .models import (
    ShippingCarrier, FreightRateMatrix, FreightConsignment,
    FreightConsignmentItem, TransitMilestoneCheckpoint, FreightShippingInvoice
)

@admin.register(ShippingCarrier)
class ShippingCarrierAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'carrier_type', 'tracking_url_template', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('carrier_type', 'is_active')

@admin.register(FreightRateMatrix)
class FreightRateMatrixAdmin(admin.ModelAdmin):
    list_display = ('carrier', 'transport_mode', 'origin_zone', 'destination_zone', 'rate_per_kg', 'fuel_surcharge_percentage', 'is_active')
    list_filter = ('transport_mode', 'carrier')

class FreightConsignmentItemInline(admin.TabularInline):
    model = FreightConsignmentItem
    extra = 1

class TransitMilestoneCheckpointInline(admin.TabularInline):
    model = TransitMilestoneCheckpoint
    extra = 1

@admin.register(FreightConsignment)
class FreightConsignmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'carrier', 'transport_mode', 'shipper_name', 'consignee_name', 'origin_hub', 'destination_hub', 'status', 'booking_date')
    search_fields = ('tracking_number', 'shipper_name', 'consignee_name', 'origin_hub', 'destination_hub')
    list_filter = ('transport_mode', 'status', 'carrier')
    inlines = [FreightConsignmentItemInline, TransitMilestoneCheckpointInline]

@admin.register(FreightShippingInvoice)
class FreightShippingInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'consignment', 'base_freight_charge', 'grand_total', 'status', 'created_at')
    list_filter = ('status',)
