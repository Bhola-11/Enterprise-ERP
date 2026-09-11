from django.contrib import admin
from .models import MasterProductionSchedule, SafetyStockRule, MRPRun, MRPRequirementItem

@admin.register(MasterProductionSchedule)
class MasterProductionScheduleAdmin(admin.ModelAdmin):
    list_display = ('product', 'period_start', 'period_end', 'planned_production_qty', 'status')
    list_filter = ('status',)

@admin.register(SafetyStockRule)
class SafetyStockRuleAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'min_safety_stock', 'reorder_point', 'economic_order_quantity', 'is_active')
    list_filter = ('is_active', 'warehouse')

class MRPRequirementItemInline(admin.TabularInline):
    model = MRPRequirementItem
    extra = 0

@admin.register(MRPRun)
class MRPRunAdmin(admin.ModelAdmin):
    list_display = ('run_number', 'planning_horizon_days', 'total_planned_orders_count', 'status', 'created_at')
    list_filter = ('status',)
    inlines = [MRPRequirementItemInline]

@admin.register(MRPRequirementItem)
class MRPRequirementItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'mrp_run', 'requirement_date', 'gross_requirement', 'net_requirement', 'order_action', 'planned_order_qty', 'order_release_date', 'status')
    list_filter = ('order_action', 'status')
