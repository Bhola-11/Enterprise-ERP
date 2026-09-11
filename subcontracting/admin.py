from django.contrib import admin
from .models import (
    SubcontractorVendor, SubcontractOrder, SubcontractMaterialDispatch,
    SubcontractGoodsReceipt
)

@admin.register(SubcontractorVendor)
class SubcontractorVendorAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'contact_person', 'contact_phone', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)

class SubcontractMaterialDispatchInline(admin.TabularInline):
    model = SubcontractMaterialDispatch
    extra = 1

class SubcontractGoodsReceiptInline(admin.TabularInline):
    model = SubcontractGoodsReceipt
    extra = 0

@admin.register(SubcontractOrder)
class SubcontractOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'subcontractor', 'finished_product', 'planned_quantity', 'total_service_cost', 'status', 'order_date')
    list_filter = ('status', 'subcontractor')
    inlines = [SubcontractMaterialDispatchInline, SubcontractGoodsReceiptInline]

@admin.register(SubcontractGoodsReceipt)
class SubcontractGoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'order', 'quantity_received', 'actual_yield_percentage', 'receipt_date')
