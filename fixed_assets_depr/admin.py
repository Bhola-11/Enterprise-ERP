from django.contrib import admin
from .models import DepreciableAsset, AssetDepreciationPeriod, AssetImpairmentRecord, AssetDisposalRecord

class AssetDepreciationPeriodInline(admin.TabularInline):
    model = AssetDepreciationPeriod
    extra = 0
    readonly_fields = ('period_date', 'opening_book_value', 'depreciation_amount', 'closing_book_value', 'is_posted', 'journal_entry')

class AssetImpairmentRecordInline(admin.TabularInline):
    model = AssetImpairmentRecord
    extra = 0
    readonly_fields = ('test_date', 'carrying_amount_before', 'recoverable_amount', 'impairment_loss', 'reason', 'journal_entry')

class AssetDisposalRecordInline(admin.TabularInline):
    model = AssetDisposalRecord
    extra = 0
    readonly_fields = ('disposal_date', 'sale_proceeds', 'net_book_value_at_disposal', 'gain_loss_amount', 'buyer_name', 'journal_entry')

@admin.register(DepreciableAsset)
class DepreciableAssetAdmin(admin.ModelAdmin):
    list_display = ('asset_tag', 'asset_name', 'category_name', 'depreciation_method', 'acquisition_cost', 'net_book_value', 'status')
    list_filter = ('status', 'depreciation_method', 'category_name')
    search_fields = ('asset_tag', 'asset_name', 'location_facility')
    inlines = [AssetDepreciationPeriodInline, AssetImpairmentRecordInline, AssetDisposalRecordInline]

@admin.register(AssetDepreciationPeriod)
class AssetDepreciationPeriodAdmin(admin.ModelAdmin):
    list_display = ('asset', 'period_date', 'depreciation_amount', 'closing_book_value', 'is_posted')
    list_filter = ('is_posted', 'period_date')

@admin.register(AssetImpairmentRecord)
class AssetImpairmentRecordAdmin(admin.ModelAdmin):
    list_display = ('asset', 'test_date', 'carrying_amount_before', 'recoverable_amount', 'impairment_loss')

@admin.register(AssetDisposalRecord)
class AssetDisposalRecordAdmin(admin.ModelAdmin):
    list_display = ('asset', 'disposal_date', 'sale_proceeds', 'gain_loss_amount', 'buyer_name')
