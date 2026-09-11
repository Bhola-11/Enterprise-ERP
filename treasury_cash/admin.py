from django.contrib import admin
from .models import CashPoolHeader, CashPoolParticipant, CashSweepingExecution, LiquidityForecast, FXHedgingContract

@admin.register(CashPoolHeader)
class CashPoolHeaderAdmin(admin.ModelAdmin):
    list_display = ('name', 'pool_code', 'pool_method', 'pool_leader_bank', 'target_balance_amount', 'is_active')

@admin.register(CashPoolParticipant)
class CashPoolParticipantAdmin(admin.ModelAdmin):
    list_display = ('pool', 'bank_account', 'priority', 'min_transfer_threshold', 'is_active')

@admin.register(CashSweepingExecution)
class CashSweepingExecutionAdmin(admin.ModelAdmin):
    list_display = ('execution_number', 'pool', 'total_swept_in', 'total_swept_out', 'transfers_count', 'created_at')

@admin.register(LiquidityForecast)
class LiquidityForecastAdmin(admin.ModelAdmin):
    list_display = ('forecast_name', 'start_date', 'end_date', 'opening_cash_balance', 'projected_closing_balance', 'net_cash_variance')

@admin.register(FXHedgingContract)
class FXHedgingContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'contract_type', 'counterparty_bank', 'notional_amount', 'base_currency', 'strike_rate', 'maturity_date', 'status')
    list_filter = ('contract_type', 'status')