from django.contrib import admin
from .models import Customer, Quotation, QuotationItem, SalesOrder, SalesOrderItem, Invoice, InvoiceItem, Payment, CreditNote

class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quote_number', 'customer', 'date', 'total_amount', 'status')
    list_filter = ('status', 'date')
    inlines = [QuotationItemInline]

class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'order_date', 'total_amount', 'status')
    list_filter = ('status', 'order_date')
    inlines = [SalesOrderItemInline]

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'invoice_date', 'total_amount', 'paid_amount', 'balance_due', 'status')
    list_filter = ('status', 'invoice_date')
    inlines = [InvoiceItemInline]

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'company_name', 'email', 'phone', 'city', 'credit_limit', 'is_active')
    search_fields = ('first_name', 'last_name', 'company_name', 'email')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'invoice', 'customer', 'payment_date', 'amount', 'payment_method')
