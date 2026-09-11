import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from sales.models import Customer
from accounting.models import JournalEntry

class PropertyComplex(models.Model):
    PROPERTY_TYPES = [
        ('COMMERCIAL_OFFICE', 'Commercial Office Tower'),
        ('RESIDENTIAL_APARTMENTS', 'Residential Multi-Family Complex'),
        ('RETAIL_MALL', 'Retail Shopping Center / Mall'),
        ('INDUSTRIAL_PARK', 'Industrial Logistics Park'),
        ('MIXED_USE', 'Mixed-Use Commercial & Residential'),
    ]
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    property_type = models.CharField(max_length=30, choices=PROPERTY_TYPES, default='COMMERCIAL_OFFICE')
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    total_floors = models.PositiveIntegerField(default=1)
    total_units_count = models.PositiveIntegerField(default=0)
    manager_name = models.CharField(max_length=150, blank=True)
    manager_phone = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.city})"

    class Meta:
        verbose_name_plural = "Property Complexes"


class PropertyUnit(models.Model):
    UNIT_TYPES = [
        ('OFFICE_SUITE', 'Executive Office Suite'),
        ('APARTMENT_1BHK', '1-Bedroom Apartment'),
        ('APARTMENT_2BHK', '2-Bedroom Apartment'),
        ('APARTMENT_PENTHOUSE', 'Luxury Penthouse'),
        ('RETAIL_SHOP', 'Ground Floor Retail Storefront'),
        ('WAREHOUSE_BAY', 'Warehouse Storage Bay'),
    ]
    OCCUPANCY_CHOICES = [
        ('VACANT', 'Vacant / Ready to Lease'),
        ('LEASED', 'Occupied / Leased'),
        ('UNDER_MAINTENANCE', 'Under Renovation / Maintenance'),
        ('RESERVED', 'Reserved / LOI Signed'),
    ]
    complex = models.ForeignKey(PropertyComplex, on_delete=models.CASCADE, related_name='units')
    unit_number = models.CharField(max_length=50) # e.g. Suite 402
    floor_number = models.PositiveIntegerField(default=1)
    unit_type = models.CharField(max_length=30, choices=UNIT_TYPES, default='OFFICE_SUITE')
    square_feet = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1000.00'))
    base_monthly_rent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('2500.00'))
    cam_fee_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('250.00')) # Common Area Maintenance
    security_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('5000.00'))
    occupancy_status = models.CharField(max_length=20, choices=OCCUPANCY_CHOICES, default='VACANT')
    amenities = models.TextField(blank=True) # HVAC, High-speed fiber, balcony, parking spots
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('complex', 'unit_number')

    def __str__(self):
        return f"{self.complex.name} - {self.unit_number} ({self.get_occupancy_status_display()})"


class PropertyTenant(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenant_profiles')
    company_or_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50)
    tax_id_or_ssn = models.CharField(max_length=50, blank=True)
    emergency_contact = models.CharField(max_length=150, blank=True)
    is_corporate = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_or_name


class LeaseAgreement(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft Proposal'),
        ('ACTIVE', 'Active In-Force'),
        ('EXPIRED', 'Naturally Expired'),
        ('TERMINATED', 'Early Terminated'),
    ]
    lease_number = models.CharField(max_length=50, unique=True)
    unit = models.ForeignKey(PropertyUnit, on_delete=models.PROTECT, related_name='leases')
    tenant = models.ForeignKey(PropertyTenant, on_delete=models.PROTECT, related_name='leases')
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2)
    cam_fee_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    security_deposit_held = models.DecimalField(max_digits=12, decimal_places=2)
    annual_escalation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00')) # 5% per annum
    payment_due_day = models.PositiveSmallIntegerField(default=1) # 1st of every month
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    terms_and_conditions = models.TextField(blank=True)
    signed_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"LEASE-{self.lease_number}: {self.unit} ({self.tenant.company_or_name})"


class TenantRentInvoice(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    invoice_number = models.CharField(max_length=50, unique=True)
    lease = models.ForeignKey(LeaseAgreement, on_delete=models.CASCADE, related_name='rent_invoices')
    period_start = models.DateField()
    period_end = models.DateField()
    base_rent = models.DecimalField(max_digits=12, decimal_places=2)
    cam_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    utility_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    due_date = models.DateField()
    paid_date = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.lease.unit.unit_number} (${self.total_amount})"


class MaintenanceWorkOrder(models.Model):
    CATEGORY_CHOICES = [
        ('PLUMBING', 'Plumbing & Drainage'),
        ('ELECTRICAL', 'Electrical & Lighting'),
        ('HVAC', 'HVAC Air Conditioning & Heating'),
        ('STRUCTURAL', 'Carpentry & Structural'),
        ('JANITORIAL', 'Janitorial & Cleaning'),
        ('ELEVATOR', 'Elevator / Lift Service'),
        ('FIRE_SAFETY', 'Fire Alarm & Safety'),
    ]
    PRIORITY_CHOICES = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Urgent'),
        ('EMERGENCY', 'Critical Emergency'),
    ]
    STATUS_CHOICES = [
        ('REPORTED', 'Work Order Logged'),
        ('ASSIGNED', 'Assigned to Vendor / Tech'),
        ('IN_PROGRESS', 'Work In Progress'),
        ('COMPLETED', 'Completed & Inspected'),
        ('CANCELLED', 'Cancelled'),
    ]
    work_order_number = models.CharField(max_length=50, unique=True)
    unit = models.ForeignKey(PropertyUnit, on_delete=models.CASCADE, related_name='work_orders')
    tenant = models.ForeignKey(PropertyTenant, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')
    issue_title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='PLUMBING')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REPORTED')
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    assigned_technician = models.CharField(max_length=150, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.work_order_number}: {self.issue_title} ({self.get_status_display()})"
