from django.contrib import admin
from .models import ConsolidationGroup, CurrencyExchangeRate, InterCompanyEliminationRule, ConsolidatedStatement

@admin.register(ConsolidationGroup)
class ConsolidationGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent_organization', 'reporting_currency', 'is_active')

@admin.register(CurrencyExchangeRate)
class CurrencyExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('effective_date', 'from_currency', 'to_currency', 'spot_rate', 'closing_rate')
    list_filter = ('from_currency', 'to_currency')

@admin.register(InterCompanyEliminationRule)
class InterCompanyEliminationRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_name', 'group', 'rule_type', 'source_account_code', 'offset_account_code', 'is_active')

@admin.register(ConsolidatedStatement)
class ConsolidatedStatementAdmin(admin.ModelAdmin):
    list_display = ('statement_number', 'group', 'statement_type', 'period_end', 'net_consolidated_total', 'status')
    list_filter = ('statement_type', 'status')