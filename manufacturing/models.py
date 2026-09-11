from django.db import models
from django.conf import settings
from decimal import Decimal
from inventory.models import Product

class WorkCenter(models.Model):
    name = models.CharField(max_length=150) # Assembly Line 1, CNC Milling, Paint Shop
    code = models.CharField(max_length=30, unique=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    capacity_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=16.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class BillOfMaterials(models.Model):
    bom_number = models.CharField(max_length=50, unique=True) # e.g. BOM-NX-100
    finished_product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='boms')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1.00)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Bills of Materials'

    def __str__(self):
        return f"BOM #{self.bom_number}: {self.finished_product.name} (Qty: {self.quantity})"

    @property
    def total_raw_material_cost(self):
        return sum(item.total_cost for item in self.items.all())

class BOMItem(models.Model):
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='items')
    raw_material = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='bom_consumptions')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    scrap_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    @property
    def total_cost(self):
        return self.quantity * self.raw_material.cost_price

    def __str__(self):
        return f"{self.raw_material.sku} x {self.quantity} for BOM #{self.bom.bom_number}"

class ProductionOrder(models.Model):
    STATUS_CHOICES = [
        ('PLANNED', 'Planned / Scheduled'),
        ('IN_PROGRESS', 'In Production / Assembling'),
        ('QC_PENDING', 'Pending Quality Inspection'),
        ('COMPLETED', 'Finished Goods Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True) # e.g. MO-2026-001
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.PROTECT, related_name='production_orders')
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT, null=True, blank=True)
    quantity_to_produce = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"MO #{self.order_number}: {self.bom.finished_product.name} x {self.quantity_to_produce} ({self.get_status_display()})"

class QualityInspection(models.Model):
    production_order = models.OneToOneField(ProductionOrder, on_delete=models.CASCADE, related_name='inspection')
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    inspection_date = models.DateField(auto_now_add=True)
    sample_size = models.PositiveIntegerField(default=10)
    passed_units = models.PositiveIntegerField(default=10)
    failed_units = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        status = "PASSED" if self.passed else "FAILED"
        return f"QC for MO #{self.production_order.order_number}: {status}"
