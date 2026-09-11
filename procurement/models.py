from django.db import models
from django.conf import settings

class ProcurementCategory(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Procurement Categories'

    def __str__(self):
        return f"{self.name} ({self.code})"

class VendorEvaluation(models.Model):
    vendor_name = models.CharField(max_length=150)
    category = models.ForeignKey(ProcurementCategory, on_delete=models.SET_NULL, null=True, blank=True)
    quality_score = models.PositiveSmallIntegerField(default=80) # 0 - 100
    delivery_score = models.PositiveSmallIntegerField(default=85) # 0 - 100
    pricing_score = models.PositiveSmallIntegerField(default=75) # 0 - 100
    compliance_score = models.PositiveSmallIntegerField(default=90) # 0 - 100
    evaluation_date = models.DateField(auto_now_add=True)
    evaluated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True, null=True)

    @property
    def composite_score(self):
        return round((self.quality_score * 0.35) + (self.delivery_score * 0.25) + (self.pricing_score * 0.25) + (self.compliance_score * 0.15), 1)

    def __str__(self):
        return f"{self.vendor_name} - Score: {self.composite_score}%"

class SpendingLimit(models.Model):
    role = models.CharField(max_length=50)
    max_approval_amount = models.DecimalField(max_digits=15, decimal_places=2)
    requires_board_approval_above = models.DecimalField(max_digits=15, decimal_places=2, default=100000.00)

    def __str__(self):
        return f"{self.role} Limit: ${self.max_approval_amount:,.2f}"
