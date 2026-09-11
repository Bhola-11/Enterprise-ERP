import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

class InspectionPlan(models.Model):
    CATEGORY_CHOICES = [
        ('INWARD_GRN', 'Inward Raw Material / Vendor GRN Gate'),
        ('IN_PROCESS', 'In-Process Shop Floor Routing Checkpoint'),
        ('FINAL_DISPATCH', 'Final Pre-Dispatch QA Gate'),
    ]
    SAMPLING_CHOICES = [
        ('AQL_1_0', 'AQL 1.0 (High Precision / Tightened)'),
        ('AQL_2_5', 'AQL 2.5 (Standard Industrial Normal)'),
        ('AQL_4_0', 'AQL 4.0 (General Commercial Reduced)'),
        ('FULL_100', '100% Full Lot Inspection'),
    ]
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='INWARD_GRN')
    sampling_standard = models.CharField(max_length=20, choices=SAMPLING_CHOICES, default='AQL_2_5')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Quality Inspection Plan'
        verbose_name_plural = 'Quality Inspection Plans'

    def __str__(self):
        return f"{self.code}: {self.name} ({self.get_category_display()})"


class InspectionCharacteristic(models.Model):
    plan = models.ForeignKey(InspectionPlan, on_delete=models.CASCADE, related_name='characteristics')
    parameter_name = models.CharField(max_length=150) # e.g. Tensile Strength, Inner Diameter, Resistance, Visual Defect
    measurement_unit = models.CharField(max_length=30, default='mm') # mm, kg/cm2, Ohms, V, count
    min_acceptable_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    max_acceptable_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    is_critical = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.parameter_name} [{self.min_acceptable_value or '-'} to {self.max_acceptable_value or '-'}] {self.measurement_unit}"


class QualityInspectionTicket(models.Model):
    DISPOSITION_CHOICES = [
        ('ACCEPTED', 'Accepted / Released to Stock'),
        ('REJECTED', 'Rejected / Quarantined'),
        ('ACCEPTED_DEVIATION', 'Accepted Under Engineering Deviation'),
        ('REWORK', 'Returned to Shop Floor for Rework'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Inspection Sampling'),
        ('IN_TESTING', 'Testing / Measurement In Progress'),
        ('COMPLETED', 'Inspection Complete & Certified'),
    ]
    ticket_number = models.CharField(max_length=50, unique=True)
    plan = models.ForeignKey(InspectionPlan, on_delete=models.PROTECT, related_name='tickets')
    reference_type = models.CharField(max_length=50, default='GRN') # GRN, PRODUCTION_ORDER, SALES_ORDER
    reference_code = models.CharField(max_length=100) # e.g. GRN-2026-0001, MO-2026-001
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    lot_size = models.PositiveIntegerField(default=100)
    sample_size = models.PositiveIntegerField(default=13)
    inspected_quantity = models.PositiveIntegerField(default=13)
    accepted_quantity = models.PositiveIntegerField(default=13)
    rejected_quantity = models.PositiveIntegerField(default=0)
    disposition = models.CharField(max_length=30, choices=DISPOSITION_CHOICES, default='ACCEPTED')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    inspection_date = models.DateField(default=timezone.now)
    inspector_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quality Inspection Ticket'
        verbose_name_plural = 'Quality Inspection Tickets'

    def __str__(self):
        return f"{self.ticket_number} - {self.reference_code} [{self.get_disposition_display()}]"


class InspectionResultMetric(models.Model):
    ticket = models.ForeignKey(QualityInspectionTicket, on_delete=models.CASCADE, related_name='metrics')
    characteristic = models.ForeignKey(InspectionCharacteristic, on_delete=models.CASCADE)
    observed_value = models.DecimalField(max_digits=10, decimal_places=3)
    is_conforming = models.BooleanField(default=True)
    remarks = models.CharField(max_length=255, blank=True)

    def __str__(self):
        status = "PASS" if self.is_conforming else "FAIL"
        return f"{self.characteristic.parameter_name}: {self.observed_value} ({status})"


class NonConformanceReport(models.Model):
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical Defect (Safety / Zero Tolerance)'),
        ('MAJOR', 'Major Defect (Functional Failure)'),
        ('MINOR', 'Minor Defect (Cosmetic / Packaging)'),
    ]
    STATUS_CHOICES = [
        ('OPEN', 'Open Defect Logged'),
        ('UNDER_INVESTIGATION', 'Under 5-Why / Ishikawa Investigation'),
        ('CAPA_INITIATED', 'CAPA Action Plan Formulated'),
        ('CLOSED', 'Verified & Closed'),
    ]
    ncr_number = models.CharField(max_length=50, unique=True)
    ticket = models.ForeignKey(QualityInspectionTicket, on_delete=models.CASCADE, related_name='ncrs')
    defect_title = models.CharField(max_length=200)
    defect_severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MAJOR')
    defect_description = models.TextField()
    root_cause_analysis = models.TextField(blank=True)
    containment_action = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='OPEN')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Non-Conformance Report (NCR)'
        verbose_name_plural = 'Non-Conformance Reports (NCR)'

    def __str__(self):
        return f"{self.ncr_number}: {self.defect_title} ({self.get_severity_display()})"


class CAPAAction(models.Model):
    TYPE_CHOICES = [
        ('CORRECTIVE', 'Corrective Action (Immediate Fix)'),
        ('PREVENTIVE', 'Preventive Action (Systemic Recurrence Prevention)'),
    ]
    ncr = models.ForeignKey(NonConformanceReport, on_delete=models.CASCADE, related_name='capas')
    action_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='CORRECTIVE')
    action_description = models.TextField()
    assigned_owner = models.CharField(max_length=150)
    target_due_date = models.DateField()
    verification_evidence = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CAPA for {self.ncr.ncr_number} ({self.get_action_type_display()}) - {self.assigned_owner}"
