from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from organizations.models import Organization
from sales.models import Customer
from inventory.models import Product, StockMovement

class ServiceTerritory(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='service_territories')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=100)
    country_code = models.CharField(max_length=10, default='US')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class ServiceTechnician(models.Model):
    SKILL_CHOICES = [
        ('APPRENTICE', 'Apprentice Technician (Level 1)'),
        ('JOURNEYMAN', 'Journeyman Specialist (Level 2)'),
        ('SENIOR_SPECIALIST', 'Senior Systems Specialist (Level 3)'),
        ('MASTER_ENGINEER', 'Master Field Systems Engineer (Level 4)'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='technicians')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='technician_profile')
    technician_code = models.CharField(max_length=50, unique=True)
    primary_territory = models.ForeignKey(ServiceTerritory, on_delete=models.SET_NULL, null=True, blank=True, related_name='technicians')
    skill_level = models.CharField(max_length=30, choices=SKILL_CHOICES, default='JOURNEYMAN')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('85.00'))
    is_available = models.BooleanField(default=True)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ['technician_code']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.technician_code})"


class WorkOrder(models.Model):
    PRIORITY_CHOICES = [
        ('CRITICAL_EMERGENCY', 'Critical Emergency (2-Hour SLA)'),
        ('HIGH', 'High Priority (4-Hour SLA)'),
        ('MEDIUM', 'Medium (Next Business Day)'),
        ('LOW', 'Low Priority (Scheduled Maintenance)'),
    ]

    STATUS_CHOICES = [
        ('UNASSIGNED', 'Unassigned / Pending Dispatch'),
        ('DISPATCHED', 'Dispatched to Technician'),
        ('EN_ROUTE', 'En Route to Site'),
        ('ON_SITE', 'Technician On Site'),
        ('WORK_IN_PROGRESS', 'Work in Progress'),
        ('COMPLETED', 'Completed & Signed Off'),
        ('CANCELLED', 'Cancelled'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='work_orders')
    work_order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='fsm_work_orders')
    territory = models.ForeignKey(ServiceTerritory, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')
    assigned_technician = models.ForeignKey(ServiceTechnician, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES, default='HIGH')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='UNASSIGNED')
    sla_deadline = models.DateTimeField()
    scheduled_start = models.DateTimeField(default=timezone.now)
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    issue_summary = models.CharField(max_length=255)
    detailed_description = models.TextField()
    resolution_notes = models.TextField(blank=True)
    service_address = models.TextField(default='Customer Industrial Facility')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"WO #{self.work_order_number} - {self.issue_summary}"


class PartConsumption(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='consumed_parts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='fsm_consumptions')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2)
    inventory_deducted = models.BooleanField(default=False)
    consumed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} for {self.work_order.work_order_number}"


class CustomerSignoff(models.Model):
    work_order = models.OneToOneField(WorkOrder, on_delete=models.CASCADE, related_name='signoff')
    signatory_name = models.CharField(max_length=100)
    signatory_title = models.CharField(max_length=100, blank=True)
    satisfaction_rating = models.PositiveIntegerField(default=5) # 1-5
    feedback_notes = models.TextField(blank=True)
    digital_signature_hash = models.CharField(max_length=64)
    signed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Signoff for WO #{self.work_order.work_order_number} ({self.satisfaction_rating} Stars)"
