from django.contrib import admin
from .models import (
    ServiceTerritory, ServiceTechnician, WorkOrder, PartConsumption, CustomerSignoff
)

class PartConsumptionInline(admin.TabularInline):
    model = PartConsumption
    extra = 1

@admin.register(ServiceTerritory)
class ServiceTerritoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'city', 'country_code', 'is_active']
    list_filter = ['country_code', 'is_active']

@admin.register(ServiceTechnician)
class ServiceTechnicianAdmin(admin.ModelAdmin):
    list_display = ['technician_code', 'user', 'skill_level', 'primary_territory', 'is_available', 'hourly_rate']
    list_filter = ['skill_level', 'is_available']

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['work_order_number', 'customer', 'assigned_technician', 'priority', 'status', 'sla_deadline']
    list_filter = ['priority', 'status']
    inlines = [PartConsumptionInline]

@admin.register(CustomerSignoff)
class CustomerSignoffAdmin(admin.ModelAdmin):
    list_display = ['work_order', 'signatory_name', 'satisfaction_rating', 'signed_at']
    list_filter = ['satisfaction_rating']
