from django.contrib import admin
from .models import (
    B2BAccount, B2BCatalogPriceTier, QuoteApprovalRequest,
    SelfServiceOrder, SelfServiceOrderItem, DigitalPaymentTransaction
)

class SelfServiceOrderItemInline(admin.TabularInline):
    model = SelfServiceOrderItem
    extra = 1

@admin.register(B2BAccount)
class B2BAccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'customer', 'credit_limit', 'credit_balance_used', 'payment_terms', 'is_active']
    search_fields = ['account_number', 'customer__name']
    list_filter = ['payment_terms', 'is_active']

@admin.register(B2BCatalogPriceTier)
class B2BCatalogPriceTierAdmin(admin.ModelAdmin):
    list_display = ['product', 'b2b_account', 'min_quantity', 'tier_unit_price', 'discount_percentage', 'is_active']
    list_filter = ['is_active']

@admin.register(QuoteApprovalRequest)
class QuoteApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['quotation', 'b2b_account', 'status', 'decided_at', 'created_at']
    list_filter = ['status']

@admin.register(SelfServiceOrder)
class SelfServiceOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'b2b_account', 'po_reference_number', 'status', 'total_amount', 'created_at']
    list_filter = ['status']
    inlines = [SelfServiceOrderItemInline]

@admin.register(DigitalPaymentTransaction)
class DigitalPaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_reference', 'b2b_account', 'amount', 'currency', 'payment_gateway', 'status', 'created_at']
    list_filter = ['payment_gateway', 'status']
