import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from accounting.models import BankAccount, Account, JournalEntry

class CashPoolHeader(models.Model):
    POOL_METHODS = [
        ('ZERO_BALANCE_SWEEP', 'Zero-Balance Account (ZBA) Sweeping'),
        ('TARGET_BALANCE_SWEEP', 'Target Balance Concentration Sweeping'),
        ('NOTIONAL_POOLING', 'Multi-Currency Notional Pooling'),
    ]
    name = models.CharField(max_length=200)
    pool_code = models.CharField(max_length=50, unique=True)
    pool_method = models.CharField(max_length=30, choices=POOL_METHODS, default='TARGET_BALANCE_SWEEP')
    pool_leader_bank = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='led_cash_pools')
    target_balance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('50000.00'))
    currency = models.CharField(max_length=10, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Cash Concentration Pool'
        verbose_name_plural = 'Cash Concentration Pools'

    def __str__(self):
        return f"{self.name} ({self.pool_code}) - Leader: {self.pool_leader_bank.bank_name}"


class CashPoolParticipant(models.Model):
    pool = models.ForeignKey(CashPoolHeader, on_delete=models.CASCADE, related_name='participants')
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='cash_pool_participations')
    priority = models.PositiveIntegerField(default=1)
    min_transfer_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('5000.00'))
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('pool', 'bank_account')
        ordering = ['priority']
        verbose_name = 'Cash Pool Participant Account'
        verbose_name_plural = 'Cash Pool Participant Accounts'

    def __str__(self):
        return f"{self.bank_account.bank_name} in {self.pool.name} (Priority {self.priority})"


class CashSweepingExecution(models.Model):
    execution_number = models.CharField(max_length=50, unique=True)
    pool = models.ForeignKey(CashPoolHeader, on_delete=models.CASCADE, related_name='sweeping_executions')
    total_swept_in = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_swept_out = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    transfers_count = models.PositiveIntegerField(default=0)
    transfers_data = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, default='COMPLETED')
    executed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cash Sweeping Execution Run'
        verbose_name_plural = 'Cash Sweeping Execution Runs'

    def __str__(self):
        return f"{self.execution_number} on {self.pool.name} (Swept In: ${self.total_swept_in})"


class LiquidityForecast(models.Model):
    forecast_name = models.CharField(max_length=200)
    forecast_period_days = models.PositiveIntegerField(default=90)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    opening_cash_balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    projected_inflows_ar = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    projected_outflows_ap = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    projected_payroll_tax = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    projected_closing_balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    net_cash_variance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Treasury Liquidity Forecast'
        verbose_name_plural = 'Treasury Liquidity Forecasts'

    def __str__(self):
        return f"{self.forecast_name} ({self.start_date} to {self.end_date})"


class FXHedgingContract(models.Model):
    CONTRACT_TYPES = [
        ('FORWARD', 'FX Outright Forward Contract'),
        ('OPTION', 'Currency Collar / Vanilla Option'),
        ('CURRENCY_SWAP', 'Cross-Currency Interest Rate Swap'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active / In-Effect'),
        ('SETTLED', 'Matured & Settled'),
        ('EXPIRED', 'Expired / Closed'),
    ]

    contract_number = models.CharField(max_length=50, unique=True)
    contract_type = models.CharField(max_length=30, choices=CONTRACT_TYPES, default='FORWARD')
    counterparty_bank = models.CharField(max_length=150) # e.g. J.P. Morgan, Citi
    notional_amount = models.DecimalField(max_digits=15, decimal_places=2)
    base_currency = models.CharField(max_length=10, default='EUR')
    quote_currency = models.CharField(max_length=10, default='USD')
    strike_rate = models.DecimalField(max_digits=12, decimal_places=6)
    maturity_date = models.DateField()
    mark_to_market_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-maturity_date']
        verbose_name = 'FX Hedging Contract'
        verbose_name_plural = 'FX Hedging Contracts'

    def __str__(self):
        return f"{self.contract_number}: {self.base_currency}/{self.quote_currency} ${self.notional_amount} @ {self.strike_rate}"