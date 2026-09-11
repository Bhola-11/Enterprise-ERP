from django.db import models
from django.conf import settings
from organizations.models import Branch
from inventory.models import Product

class Warehouse(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    manager = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    total_capacity_sqft = models.PositiveIntegerField(default=10000)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Zone(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=50) # e.g. Zone A (Cold Storage), Zone B (Dry Goods)
    code = models.CharField(max_length=20)
    temperature_controlled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.warehouse.code} - {self.name}"

class Bin(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='bins')
    aisle = models.CharField(max_length=20) # e.g. A01
    shelf = models.CharField(max_length=20) # e.g. S03
    bin_number = models.CharField(max_length=20) # e.g. B12
    max_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)

    class Meta:
        unique_together = ('zone', 'aisle', 'shelf', 'bin_number')

    def __str__(self):
        return f"{self.zone.warehouse.code}/{self.zone.code}-{self.aisle}-{self.shelf}-{self.bin_number}"

class StockTransfer(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('IN_TRANSIT', 'In Transit'),
        ('COMPLETED', 'Completed & Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    transfer_number = models.CharField(max_length=50, unique=True)
    source_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='outgoing_transfers')
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='incoming_transfers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    transfer_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transfer #{self.transfer_number}: {self.source_warehouse.code} -> {self.destination_warehouse.code} ({self.status})"

class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} (Qty: {self.quantity})"
