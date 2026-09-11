import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from inventory.models import Product
from warehouse.models import Warehouse
from manufacturing.models import BillOfMaterials

class MasterProductionSchedule(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft Proposal'),
        ('APPROVED', 'Approved by Operations'),
        ('IN_EXECUTION', 'In-Execution on Floor'),
        ('COMPLETED', 'Schedule Fulfilled'),
    ]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='mps_entries')
    period_start = models.DateField()
    period_end = models.DateField()
    forecast_demand_qty = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    confirmed_so_qty = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    planned_production_qty = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPROVED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['period_start', 'product']
        verbose_name = 'Master Production Schedule (MPS)'
        verbose_name_plural = 'Master Production Schedules (MPS)'

    def __str__(self):
        return f"MPS: {self.product.name} ({self.period_start} to {self.period_end}) - Qty {self.planned_production_qty}"


class SafetyStockRule(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='safety_rules')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='safety_rules')
    min_safety_stock = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50.00'))
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    economic_order_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('200.00'))
    lead_time_days = models.PositiveIntegerField(default=7)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('product', 'warehouse')
        verbose_name = 'Safety Stock & Reorder Rule'
        verbose_name_plural = 'Safety Stock & Reorder Rules'

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.name} (ROP: {self.reorder_point}, EOQ: {self.economic_order_quantity})"


class MRPRun(models.Model):
    STATUS_CHOICES = [
        ('RUNNING', 'Computation Running'),
        ('COMPLETED', 'Calculated & Ready'),
        ('APPLIED', 'Orders Released to Supply Chain'),
        ('CANCELLED', 'Cancelled / Discarded'),
    ]
    run_number = models.CharField(max_length=50, unique=True)
    planning_horizon_days = models.PositiveIntegerField(default=90)
    include_forecast = models.BooleanField(default=True)
    include_safety_stock = models.BooleanField(default=True)
    total_planned_orders_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    executed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'MRP Run Execution'
        verbose_name_plural = 'MRP Run Executions'

    def __str__(self):
        return f"{self.run_number} ({self.created_at.strftime('%Y-%m-%d')} - {self.total_planned_orders_count} Orders)"


class MRPRequirementItem(models.Model):
    ACTION_CHOICES = [
        ('PURCHASE_ORDER', 'Generate Purchase Order (External Buy)'),
        ('PRODUCTION_ORDER', 'Generate Production / Work Order (Internal Make)'),
        ('TRANSFER', 'Generate Inter-Warehouse Transfer'),
    ]
    STATUS_CHOICES = [
        ('RECOMMENDED', 'MRP Planned Recommendation'),
        ('RELEASED', 'Released to Purchasing / Manufacturing'),
        ('DISMISSED', 'Dismissed by Planner'),
    ]
    mrp_run = models.ForeignKey(MRPRun, on_delete=models.CASCADE, related_name='requirements')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='mrp_requirements')
    requirement_date = models.DateField()
    gross_requirement = models.DecimalField(max_digits=12, decimal_places=2)
    current_on_hand = models.DecimalField(max_digits=12, decimal_places=2)
    scheduled_receipts = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_requirement = models.DecimalField(max_digits=12, decimal_places=2)
    order_action = models.CharField(max_length=30, choices=ACTION_CHOICES, default='PURCHASE_ORDER')
    planned_order_qty = models.DecimalField(max_digits=12, decimal_places=2)
    lead_time_days = models.PositiveIntegerField(default=7)
    order_release_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECOMMENDED')

    class Meta:
        ordering = ['requirement_date', 'product']
        verbose_name = 'MRP Planned Order Requirement'
        verbose_name_plural = 'MRP Planned Order Requirements'

    def __str__(self):
        return f"{self.order_action} - {self.product.name} (Qty: {self.planned_order_qty}) on {self.order_release_date}"
