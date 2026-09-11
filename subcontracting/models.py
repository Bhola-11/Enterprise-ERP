import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from inventory.models import Product
from accounting.models import JournalEntry

class SubcontractorVendor(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    vendor_tax_id = models.CharField(max_length=50, blank=True)
    contact_person = models.CharField(max_length=150, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    facility_address = models.TextField()
    toll_processing_types = models.TextField(help_text="e.g. CNC Milling, Heat Treatment, Surface Anodizing, PCB Assembly")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Subcontractor / Job Worker'
        verbose_name_plural = 'Subcontractors / Job Workers'

    def __str__(self):
        return f"{self.code} - {self.name}"


class SubcontractOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft Work Order'),
        ('MATERIALS_DISPATCHED', 'Raw Materials Issued to Vendor'),
        ('IN_PROCESSING', 'Toll Processing In-Progress at Vendor'),
        ('PARTIALLY_RECEIVED', 'Partially Received Finished Goods'),
        ('COMPLETED', 'Completed & Reconciled'),
        ('CANCELLED', 'Cancelled'),
    ]
    order_number = models.CharField(max_length=50, unique=True)
    subcontractor = models.ForeignKey(SubcontractorVendor, on_delete=models.PROTECT, related_name='orders')
    finished_product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='subcontract_orders')
    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_processing_rate = models.DecimalField(max_digits=10, decimal_places=2)
    total_service_cost = models.DecimalField(max_digits=12, decimal_places=2)
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-order_date']
        verbose_name = 'Subcontract Work Order'
        verbose_name_plural = 'Subcontract Work Orders'

    def __str__(self):
        return f"{self.order_number}: {self.finished_product.name} x {self.planned_quantity} ({self.subcontractor.name})"


class SubcontractMaterialDispatch(models.Model):
    order = models.ForeignKey(SubcontractOrder, on_delete=models.CASCADE, related_name='dispatches')
    dispatch_challan_number = models.CharField(max_length=50, unique=True)
    raw_material = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='subcontract_dispatches')
    quantity_issued = models.DecimalField(max_digits=12, decimal_places=2)
    lot_number = models.CharField(max_length=50, default='LOT-001')
    dispatched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Challan #{self.dispatch_challan_number}: {self.raw_material.sku} x {self.quantity_issued}"


class SubcontractGoodsReceipt(models.Model):
    receipt_number = models.CharField(max_length=50, unique=True)
    order = models.ForeignKey(SubcontractOrder, on_delete=models.CASCADE, related_name='receipts')
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_rejected = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    scrap_material_reported = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    actual_yield_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    receipt_date = models.DateField(default=timezone.now)
    vendor_delivery_note_ref = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subcontract Goods Receipt Note (SGRN)'
        verbose_name_plural = 'Subcontract Goods Receipt Notes (SGRN)'

    def __str__(self):
        return f"{self.receipt_number} - {self.order.order_number}: Recv {self.quantity_received} Units"
