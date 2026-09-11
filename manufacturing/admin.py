from django.contrib import admin
from .models import WorkCenter, BillOfMaterials, BOMItem, ProductionOrder, QualityInspection

class BOMItemInline(admin.TabularInline):
    model = BOMItem
    extra = 2

@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = ('bom_number', 'finished_product', 'quantity', 'is_active')
    inlines = [BOMItemInline]

@admin.register(WorkCenter)
class WorkCenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'hourly_rate', 'capacity_hours_per_day', 'is_active')

@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'bom', 'quantity_to_produce', 'start_date', 'due_date', 'status')
    list_filter = ('status', 'start_date')

@admin.register(QualityInspection)
class QualityInspectionAdmin(admin.ModelAdmin):
    list_display = ('production_order', 'inspector', 'inspection_date', 'passed_units', 'failed_units', 'passed')
