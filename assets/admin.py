from django.contrib import admin
from .models import AssetCategory, Asset, AssetMaintenanceLog

@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'depreciation_method', 'useful_life_years', 'salvage_value_percentage')

class AssetMaintenanceLogInline(admin.TabularInline):
    model = AssetMaintenanceLog
    extra = 1

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_tag', 'name', 'category', 'purchase_cost', 'current_value', 'status', 'assigned_to')
    list_filter = ('category', 'status')
    search_fields = ('asset_tag', 'name', 'serial_number')
    inlines = [AssetMaintenanceLogInline]
