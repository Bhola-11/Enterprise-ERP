from django.contrib import admin
from .models import (
    POSTerminal, POSSession, POSCustomerLoyalty, POSCouponPromotion,
    POSOrder, POSOrderItem, POSPayment, POSCashTransaction
)


class POSOrderItemInline(admin.TabularInline):
    model = POSOrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'sku', 'barcode', 'unit_price', 'quantity', 'tax_rate', 'tax_amount', 'discount_amount', 'line_total']
    can_delete = False


class POSPaymentInline(admin.TabularInline):
    model = POSPayment
    extra = 0
    readonly_fields = ['payment_method', 'amount', 'reference_number', 'card_last4', 'status', 'timestamp']
    can_delete = False


@admin.register(POSTerminal)
class POSTerminalAdmin(admin.ModelAdmin):
    list_display = ['terminal_code', 'name', 'branch', 'warehouse', 'status', 'allow_offline_orders', 'created_at']
    list_filter = ['status', 'branch', 'allow_offline_orders']
    search_fields = ['terminal_code', 'name', 'ip_address']


@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    list_display = ['session_number', 'terminal', 'cashier', 'opening_time', 'closing_time', 'opening_cash', 'total_sales_amount', 'status']
    list_filter = ['status', 'terminal__branch', 'opening_time']
    search_fields = ['session_number', 'cashier__username', 'terminal__terminal_code']


@admin.register(POSOrder)
class POSOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'session', 'terminal', 'cashier', 'customer', 'grand_total', 'paid_amount', 'status', 'created_at']
    list_filter = ['status', 'order_type', 'terminal__branch', 'created_at']
    search_fields = ['order_number', 'customer__name', 'cashier__username']
    inlines = [POSOrderItemInline, POSPaymentInline]


@admin.register(POSCustomerLoyalty)
class POSCustomerLoyaltyAdmin(admin.ModelAdmin):
    list_display = ['customer', 'card_number', 'tier', 'points_balance', 'lifetime_spend', 'last_activity_date']
    list_filter = ['tier']
    search_fields = ['customer__name', 'card_number']


@admin.register(POSCouponPromotion)
class POSCouponPromotionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'discount_type', 'discount_value', 'valid_from', 'valid_to', 'times_used', 'usage_limit', 'is_active']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code', 'name']


@admin.register(POSCashTransaction)
class POSCashTransactionAdmin(admin.ModelAdmin):
    list_display = ['session', 'transaction_type', 'amount', 'reason', 'authorized_by', 'created_at']
    list_filter = ['transaction_type']
    search_fields = ['reason', 'session__session_number']
