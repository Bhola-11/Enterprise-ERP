from django.contrib import admin
from .models import ProcurementCategory, VendorEvaluation, SpendingLimit

@admin.register(ProcurementCategory)
class ProcurementCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(VendorEvaluation)
class VendorEvaluationAdmin(admin.ModelAdmin):
    list_display = ('vendor_name', 'category', 'quality_score', 'delivery_score', 'pricing_score', 'evaluation_date')

@admin.register(SpendingLimit)
class SpendingLimitAdmin(admin.ModelAdmin):
    list_display = ('role', 'max_approval_amount', 'requires_board_approval_above')
