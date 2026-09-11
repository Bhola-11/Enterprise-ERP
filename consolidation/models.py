import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from organizations.models import Organization
from accounting.models import Account, JournalEntry

class ConsolidationGroup(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    parent_organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='parent_consolidation_groups')
    subsidiary_organizations = models.ManyToManyField(Organization, related_name='subsidiary_consolidation_groups')
    reporting_currency = models.CharField(max_length=10, default='USD')
    fiscal_year_end_month = models.PositiveSmallIntegerField(default=12)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Consolidation Group'
        verbose_name_plural = 'Consolidation Groups'

    def __str__(self):
        return f"{self.name} ({self.reporting_currency})"


class CurrencyExchangeRate(models.Model):
    from_currency = models.CharField(max_length=10) # EUR, GBP, JPY, SGD
    to_currency = models.CharField(max_length=10, default='USD')
    effective_date = models.DateField(default=timezone.now)
    spot_rate = models.DecimalField(max_digits=12, decimal_places=6)
    average_monthly_rate = models.DecimalField(max_digits=12, decimal_places=6)
    closing_rate = models.DecimalField(max_digits=12, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_currency', 'to_currency', 'effective_date')
        ordering = ['-effective_date']
        verbose_name = 'IAS 21 Currency Exchange Rate'
        verbose_name_plural = 'IAS 21 Currency Exchange Rates'

    def __str__(self):
        return f"{self.from_currency}/{self.to_currency} on {self.effective_date} (Spot: {self.spot_rate})"


class InterCompanyEliminationRule(models.Model):
    RULE_TYPES = [
        ('AR_AP_BALANCE', 'Intercompany Accounts Receivable / Payable Elimination'),
        ('REVENUE_EXPENSE', 'Intercompany Revenue & Outside Processing Expense'),
        ('DIVIDEND_ELIM', 'Intercompany Dividend & Equity Elimination'),
        ('LOAN_INTEREST', 'Intercompany Loan & Financing Interest'),
    ]
    group = models.ForeignKey(ConsolidationGroup, on_delete=models.CASCADE, related_name='elimination_rules')
    rule_name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES, default='AR_AP_BALANCE')
    source_account_code = models.CharField(max_length=50, help_text="e.g. 1100 (Trade AR)")
    offset_account_code = models.CharField(max_length=50, help_text="e.g. 2010 (Trade AP)")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Intercompany Elimination Rule'
        verbose_name_plural = 'Intercompany Elimination Rules'

    def __str__(self):
        return f"{self.rule_name} [{self.get_rule_type_display()}]"


class ConsolidatedStatement(models.Model):
    STATEMENT_TYPES = [
        ('BALANCE_SHEET', 'Consolidated Statement of Financial Position (Balance Sheet)'),
        ('PROFIT_AND_LOSS', 'Consolidated Statement of Profit & Loss (Income Statement)'),
        ('CASH_FLOW', 'Consolidated Statement of Cash Flows'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Draft Consolidation Matrix'),
        ('ELIMINATED', 'Intercompany Eliminations Applied'),
        ('FINALIZED', 'Audited & Board Approved'),
    ]
    statement_number = models.CharField(max_length=50, unique=True)
    group = models.ForeignKey(ConsolidationGroup, on_delete=models.PROTECT, related_name='statements')
    statement_type = models.CharField(max_length=30, choices=STATEMENT_TYPES, default='BALANCE_SHEET')
    period_start = models.DateField()
    period_end = models.DateField()
    reporting_currency = models.CharField(max_length=10, default='USD')
    gross_total_parent = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    gross_total_subsidiaries = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    total_eliminations = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    net_consolidated_total = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    currency_translation_adjustment = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ELIMINATED')
    statement_data = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_end']
        verbose_name = 'Consolidated Financial Statement'
        verbose_name_plural = 'Consolidated Financial Statements'

    def __str__(self):
        return f"{self.statement_number}: {self.group.name} - {self.get_statement_type_display()} ({self.period_end})"