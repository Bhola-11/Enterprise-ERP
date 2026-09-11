from django.contrib import admin
from .models import Account, JournalEntry, JournalItem, BankAccount

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'balance', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('code', 'name')

class JournalItemInline(admin.TabularInline):
    model = JournalItem
    extra = 2

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'date', 'reference', 'total_debit', 'total_credit', 'status', 'created_by')
    list_filter = ('status', 'date')
    search_fields = ('entry_number', 'reference', 'narration')
    inlines = [JournalItemInline]

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'bank_name', 'account_number', 'balance', 'is_active')
