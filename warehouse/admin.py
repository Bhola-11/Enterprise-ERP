from django.contrib import admin
from .models import Warehouse, Zone, Bin, StockTransfer, StockTransferItem

class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 1

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'branch', 'manager', 'city', 'is_primary', 'is_active')
    list_filter = ('is_primary', 'is_active', 'branch')
    inlines = [ZoneInline]

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ('zone', 'aisle', 'shelf', 'bin_number', 'max_weight_kg')

class StockTransferItemInline(admin.TabularInline):
    model = StockTransferItem
    extra = 1

@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ('transfer_number', 'source_warehouse', 'destination_warehouse', 'transfer_date', 'status')
    list_filter = ('status', 'transfer_date')
    inlines = [StockTransferItemInline]
