from django.contrib import admin
from .models import (
    PropertyComplex, PropertyUnit, PropertyTenant, LeaseAgreement,
    TenantRentInvoice, MaintenanceWorkOrder
)

class PropertyUnitInline(admin.TabularInline):
    model = PropertyUnit
    extra = 1

@admin.register(PropertyComplex)
class PropertyComplexAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'property_type', 'city', 'total_floors', 'manager_name')
    search_fields = ('code', 'name', 'city')
    list_filter = ('property_type',)
    inlines = [PropertyUnitInline]

@admin.register(PropertyUnit)
class PropertyUnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'complex', 'unit_type', 'floor_number', 'square_feet', 'base_monthly_rent', 'occupancy_status')
    list_filter = ('occupancy_status', 'unit_type', 'complex')
    search_fields = ('unit_number',)

@admin.register(PropertyTenant)
class PropertyTenantAdmin(admin.ModelAdmin):
    list_display = ('company_or_name', 'contact_person', 'email', 'phone', 'is_corporate')
    search_fields = ('company_or_name', 'email', 'phone')

@admin.register(LeaseAgreement)
class LeaseAgreementAdmin(admin.ModelAdmin):
    list_display = ('lease_number', 'unit', 'tenant', 'start_date', 'end_date', 'monthly_rent', 'status')
    list_filter = ('status',)
    search_fields = ('lease_number',)

@admin.register(TenantRentInvoice)
class TenantRentInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'lease', 'period_start', 'total_amount', 'paid_amount', 'balance_amount', 'status', 'due_date')
    list_filter = ('status',)

@admin.register(MaintenanceWorkOrder)
class MaintenanceWorkOrderAdmin(admin.ModelAdmin):
    list_display = ('work_order_number', 'unit', 'issue_title', 'category', 'priority', 'status', 'estimated_cost', 'actual_cost')
    list_filter = ('category', 'priority', 'status')
