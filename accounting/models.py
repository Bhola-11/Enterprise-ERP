from django.db import models
from django.conf import settings
from decimal import Decimal
from organizations.models import FiscalYear, CostCenter

class Account(models.Model):
    TYPE_CHOICES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue / Income'),
        ('EXPENSE', 'Expense'),
    ]

    code = models.CharField(max_length=30, unique=True) # e.g. 1010, 1020, 2010, 4010, 5010
    name = models.CharField(max_length=150) # Cash in Bank, Accounts Receivable, Inventory, etc.
    account_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_accounts')
    description = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name} ({self.get_account_type_display()})"

class JournalEntry(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted & Locked'),
        ('VOID', 'Void / Cancelled'),
    ]

    entry_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True, null=True) # INV-001, PO-102, PAY-99
    narration = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f"JE #{self.entry_number} ({self.date}) - ${self.total_debit:,.2f} ({self.status})"

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit and self.total_debit > Decimal('0.00')

class JournalItem(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='items')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_items')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.account.name}: Dr ${self.debit} / Cr ${self.credit}"

class BankAccount(models.Model):
    account_name = models.CharField(max_length=100) # Operating Account, Payroll Account
    bank_name = models.CharField(max_length=100) # JPMorgan Chase, Silicon Valley Bank
    account_number = models.CharField(max_length=50)
    routing_number = models.CharField(max_length=50, blank=True, null=True)
    gl_account = models.OneToOneField(Account, on_delete=models.PROTECT, related_name='linked_bank_account')
    currency = models.CharField(max_length=10, default='USD')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_name} (****{self.account_number[-4:]})"
