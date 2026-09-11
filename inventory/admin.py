from django.contrib import admin
from .models import ProductCategory, ProductBrand, UnitOfMeasure, Product, Batch, StockMovement, StockAdjustment, StockAdjustmentItem

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')

@admin.register(ProductBrand)
class ProductBrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'cost_price', 'selling_price', 'current_stock', 'reorder_level', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('sku', 'name', 'barcode')

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'product', 'movement_type', 'quantity', 'balance_after', 'reference_number', 'warehouse_name')
    list_filter = ('movement_type', 'timestamp')
    search_fields = ('product__name', 'product__sku', 'reference_number')
    readonly_fields = [f.name for f in StockMovement._meta.fields]
