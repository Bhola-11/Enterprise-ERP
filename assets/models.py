from django.db import models
from django.conf import settings
from decimal import Decimal
from hr.models import Employee

class AssetCategory(models.Model):
    METHOD_CHOICES = [
        ('STRAIGHT_LINE', 'Straight-Line Depreciation'),
        ('DECLINING_BALANCE', 'Declining Balance Depreciation'),
    ]

    name = models.CharField(max_length=100) # IT Hardware, Office Furniture, Machinery, Vehicles
    depreciation_method = models.CharField(max_length=30, choices=METHOD_CHOICES, default='STRAIGHT_LINE')
    useful_life_years = models.PositiveSmallIntegerField(default=5)
    salvage_value_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)

    class Meta:
        verbose_name_plural = 'Asset Categories'

    def __str__(self):
        return f"{self.name} ({self.useful_life_years} yrs)"

class Asset(models.Model):
    STATUS_CHOICES = [
        ('IN_STORE', 'In Storage / Unassigned'),
        ('ASSIGNED', 'Assigned to Employee'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('DISPOSED', 'Disposed / Written Off'),
    ]

    asset_tag = models.CharField(max_length=50, unique=True) # e.g. AST-IT-0091
    name = models.CharField(max_length=150)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name='assets')
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    purchase_date = models.DateField()
    purchase_cost = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_STORE')
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_assets')
    location = models.CharField(max_length=100, default='Headquarters')
    warranty_expiry = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['asset_tag']

    def __str__(self):
        return f"[{self.asset_tag}] {self.name} (${self.current_value:,.2f})"

    @property
    def annual_depreciation(self):
        if self.category.useful_life_years > 0:
            depreciable = self.purchase_cost - self.salvage_value
            return depreciable / Decimal(str(self.category.useful_life_years))
        return Decimal('0.00')

class AssetMaintenanceLog(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_logs')
    date = models.DateField()
    service_type = models.CharField(max_length=100) # Preventive, Repair, Calibration
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    service_provider = models.CharField(max_length=150)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.asset.asset_tag} - {self.service_type} on {self.date}"
