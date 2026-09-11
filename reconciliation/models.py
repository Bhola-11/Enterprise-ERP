from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


class BankStatement(models.Model):
    STATEMENT_FORMATS = [
        ('CSV', 'Standard Bank CSV'),
        ('OFX', 'OFX (Open Financial Exchange)'),
        ('MT940', 'SWIFT MT940 Electronic Statement'),
        ('CAMT053', 'ISO 20022 CAMT.053 XML'),
        ('QIF', 'Quicken Interchange Format (QIF)'),
    ]

    STATUS_CHOICES = [
        ('IMPORTED', 'Imported (Pending Reconciliation)'),
        ('IN_PROGRESS', 'Reconciliation In-Progress'),
        ('RECONCILED', 'Fully Reconciled & Balanced'),
    ]

    statement_identifier = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    bank_account = models.ForeignKey('accounting.BankAccount', on_delete=models.CASCADE, related_name='bank_statements')
    statement_format = models.CharField(max_length=20, choices=STATEMENT_FORMATS, default='CSV')
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    closing_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    start_date = models.DateField()
    end_date = models.DateField()
    total_lines_count = models.PositiveIntegerField(default=0)
    reconciled_lines_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IMPORTED')
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date', '-created_at']
        verbose_name = 'Bank Statement'
        verbose_name_plural = 'Bank Statements'

    def __str__(self):
        return f"{self.bank_account.bank_name} ({self.start_date} to {self.end_date}) - {self.status}"


class BankStatementLine(models.Model):
    LINE_STATUS = [
        ('UNMATCHED', 'Unmatched / Pending'),
        ('AUTO_MATCHED', 'Auto-Matched by Rule Engine'),
        ('MANUALLY_MATCHED', 'Manually Reconciled'),
        ('IGNORED', 'Ignored / Skipped'),
    ]

    TXN_TYPES = [
        ('DEBIT', 'Debit (Cash Withdrawal / Outflow)'),
        ('CREDIT', 'Credit (Deposit / Inflow)'),
    ]

    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, related_name='lines')
    line_number = models.PositiveIntegerField()
    transaction_date = models.DateField()
    value_date = models.DateField(null=True, blank=True)
    raw_description = models.TextField()
    transaction_type = models.CharField(max_length=10, choices=TXN_TYPES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    transaction_reference = models.CharField(max_length=150, blank=True)
    counterparty_name = models.CharField(max_length=200, blank=True)
    counterparty_account = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=LINE_STATUS, default='UNMATCHED')

    matched_journal_item = models.ForeignKey('accounting.JournalItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='reconciled_statement_lines')
    matched_payment = models.ForeignKey('sales.Payment', on_delete=models.SET_NULL, null=True, blank=True, related_name='reconciled_statement_lines')
    match_confidence_score = models.PositiveIntegerField(default=0, help_text="0 to 100 confidence score")
    match_rule_applied = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['statement', 'line_number']
        verbose_name = 'Bank Statement Line'
        verbose_name_plural = 'Bank Statement Lines'

    def __str__(self):
        return f"Line {self.line_number} [{self.transaction_date}] {self.transaction_type} ${self.amount} ({self.status})"


class ReconciliationRule(models.Model):
    RULE_TYPES = [
        ('EXACT_AMOUNT_AND_DATE', 'Exact Amount & Exact Date Match'),
        ('AMOUNT_AND_REF', 'Exact Amount & Reference Match'),
        ('DESCRIPTION_REGEX', 'Description RegEx Keyword Pattern'),
        ('COUNTERPARTY_MATCH', 'Counterparty Name & Amount Match'),
        ('TOLERANT_DATE', 'Exact Amount with +/- N Days Date Tolerance'),
    ]

    name = models.CharField(max_length=150)
    priority = models.PositiveIntegerField(default=10)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES, default='EXACT_AMOUNT_AND_DATE')
    regex_pattern = models.CharField(max_length=255, blank=True, help_text="RegEx for description or reference")
    date_tolerance_days = models.PositiveIntegerField(default=3)
    min_confidence_score = models.PositiveIntegerField(default=80)
    auto_post_adjusting_entry = models.BooleanField(default=False)
    contra_account = models.ForeignKey('accounting.Account', on_delete=models.SET_NULL, null=True, blank=True, help_text="Target account for automated adjustments (e.g. Bank Fees, Interest Income)")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['priority', 'name']
        verbose_name = 'Reconciliation Rule'
        verbose_name_plural = 'Reconciliation Rules'

    def __str__(self):
        return f"Rule {self.priority}: {self.name} ({self.rule_type})"


class ReconciliationSession(models.Model):
    SESSION_STATUS = [
        ('IN_PROGRESS', 'In-Progress Audit'),
        ('BALANCED', 'Balanced & Finalized'),
    ]

    session_code = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, related_name='sessions')
    bank_account = models.ForeignKey('accounting.BankAccount', on_delete=models.CASCADE, related_name='reconciliation_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    statement_closing_balance = models.DecimalField(max_digits=14, decimal_places=2)
    system_gl_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    unreconciled_difference = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='IN_PROGRESS')
    reconciled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Reconciliation Session'
        verbose_name_plural = 'Reconciliation Sessions'

    def __str__(self):
        return f"Recon Session {self.session_code} - {self.bank_account.bank_name} ({self.status})"
