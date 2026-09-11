from django.contrib import admin
from .models import Supplier, PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GoodsReceiptItem

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

class GoodsReceiptItemInline(admin.TabularInline):
    model = GoodsReceiptItem
    extra = 1

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'city', 'payment_terms', 'rating', 'is_active')
    search_fields = ('name', 'email', 'contact_person')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'order_date', 'total_amount', 'status', 'created_by')
    list_filter = ('status', 'order_date')
    search_fields = ('po_number', 'supplier__name')
    inlines = [PurchaseOrderItemInline]

@admin.register(GoodsReceiptNote)
class GoodsReceiptNoteAdmin(admin.ModelAdmin):
    list_display = ('grn_number', 'purchase_order', 'warehouse', 'receipt_date', 'received_by')
    inlines = [GoodsReceiptItemInline]
