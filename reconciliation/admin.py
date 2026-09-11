from django.contrib import admin
from .models import (
    BankStatement, BankStatementLine, ReconciliationRule,
    ReconciliationSession
)


class BankStatementLineInline(admin.TabularInline):
    model = BankStatementLine
    extra = 0
    readonly_fields = ['line_number', 'transaction_date', 'raw_description', 'transaction_type', 'amount', 'status', 'match_confidence_score', 'match_rule_applied']
    can_delete = False


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = ['bank_account', 'statement_format', 'start_date', 'end_date', 'total_lines_count', 'reconciled_lines_count', 'status', 'created_at']
    list_filter = ['statement_format', 'status', 'bank_account']
    search_fields = ['statement_identifier', 'bank_account__bank_name']
    inlines = [BankStatementLineInline]


@admin.register(BankStatementLine)
class BankStatementLineAdmin(admin.ModelAdmin):
    list_display = ['statement', 'line_number', 'transaction_date', 'transaction_type', 'amount', 'status', 'match_confidence_score']
    list_filter = ['status', 'transaction_type', 'transaction_date']
    search_fields = ['raw_description', 'transaction_reference', 'counterparty_name']


@admin.register(ReconciliationRule)
class ReconciliationRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'priority', 'rule_type', 'date_tolerance_days', 'min_confidence_score', 'auto_post_adjusting_entry', 'is_active']
    list_filter = ['rule_type', 'is_active']
    search_fields = ['name', 'regex_pattern']


@admin.register(ReconciliationSession)
class ReconciliationSessionAdmin(admin.ModelAdmin):
    list_display = ['session_code', 'bank_account', 'started_at', 'statement_closing_balance', 'system_gl_balance', 'unreconciled_difference', 'status']
    list_filter = ['status', 'bank_account']
    search_fields = ['session_code']
