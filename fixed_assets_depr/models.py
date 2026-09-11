import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from accounting.models import Account, JournalEntry

class DepreciableAsset(models.Model):
    DEPRECIATION_METHODS = [
        ('STRAIGHT_LINE', 'Straight-Line Depreciation (IAS 16 / GAAP)'),
        ('DOUBLE_DECLINING', '200% Double-Declining Balance (Accelerated)'),
        ('MACRS_5YR', 'MACRS 5-Year Property Table (Tax Accelerated)'),
        ('MACRS_7YR', 'MACRS 7-Year Property Table (Industrial Machinery)'),
        ('SUM_OF_YEARS', 'Sum-of-the-Years Digits (SYD)'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active in Service'),
        ('FULLY_DEPRECIATED', 'Fully Depreciated (Zero Net Book Value)'),
        ('DISPOSED', 'Disposed / Sold Off'),
        ('IMPAIRED', 'Impaired per IAS 36'),
    ]

    asset_tag = models.CharField(max_length=50, unique=True)
    asset_name = models.CharField(max_length=200)
    category_name = models.CharField(max_length=100, default='Machinery & Robotics')
    acquisition_date = models.DateField()
    acquisition_cost = models.DecimalField(max_digits=15, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    useful_life_months = models.PositiveIntegerField(default=60)
    depreciation_method = models.CharField(max_length=30, choices=DEPRECIATION_METHODS, default='STRAIGHT_LINE')

    asset_gl_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+')
    accumulated_depr_gl_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+')
    depreciation_expense_gl_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='+')

    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_book_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='ACTIVE')
    location_facility = models.CharField(max_length=150, default='Main Advanced Manufacturing Plant')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-acquisition_date']
        verbose_name = 'Depreciable Fixed Asset'
        verbose_name_plural = 'Depreciable Fixed Assets'

    def __str__(self):
        return f"{self.asset_tag}: {self.asset_name} (NBV: ${self.net_book_value})"


class AssetDepreciationPeriod(models.Model):
    asset = models.ForeignKey(DepreciableAsset, on_delete=models.CASCADE, related_name='depreciation_schedule')
    period_date = models.DateField()
    opening_book_value = models.DecimalField(max_digits=15, decimal_places=2)
    depreciation_amount = models.DecimalField(max_digits=15, decimal_places=2)
    closing_book_value = models.DecimalField(max_digits=15, decimal_places=2)
    is_posted = models.BooleanField(default=False)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('asset', 'period_date')
        ordering = ['period_date']
        verbose_name = 'Asset Depreciation Period'
        verbose_name_plural = 'Asset Depreciation Periods'

    def __str__(self):
        return f"{self.asset.asset_tag} @ {self.period_date}: ${self.depreciation_amount} Depr (NBV: ${self.closing_book_value})"


class AssetImpairmentRecord(models.Model):
    asset = models.ForeignKey(DepreciableAsset, on_delete=models.CASCADE, related_name='impairments')
    test_date = models.DateField(default=timezone.now)
    carrying_amount_before = models.DecimalField(max_digits=15, decimal_places=2)
    recoverable_amount = models.DecimalField(max_digits=15, decimal_places=2)
    impairment_loss = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.TextField(help_text="Technological obsolescence, damage, or adverse market shift")
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-test_date']
        verbose_name = 'Asset Impairment Test (IAS 36)'
        verbose_name_plural = 'Asset Impairment Tests (IAS 36)'

    def __str__(self):
        return f"Impairment on {self.asset.asset_tag}: Loss of ${self.impairment_loss}"


class AssetDisposalRecord(models.Model):
    asset = models.ForeignKey(DepreciableAsset, on_delete=models.CASCADE, related_name='disposals')
    disposal_date = models.DateField(default=timezone.now)
    sale_proceeds = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_book_value_at_disposal = models.DecimalField(max_digits=15, decimal_places=2)
    gain_loss_amount = models.DecimalField(max_digits=15, decimal_places=2) # Positive = Gain, Negative = Loss
    buyer_name = models.CharField(max_length=150, blank=True)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-disposal_date']
        verbose_name = 'Asset Disposal & Derecognition'
        verbose_name_plural = 'Asset Disposals & Derecognitions'

    def __str__(self):
        outcome = "Gain" if self.gain_loss_amount >= 0 else "Loss"
        return f"Disposal of {self.asset.asset_tag}: {outcome} of ${abs(self.gain_loss_amount)}"