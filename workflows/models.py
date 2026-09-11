from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class WorkflowDefinition(models.Model):
    MODULE_CHOICES = [
        ('PURCHASE_ORDER', 'Purchase Order Approval'),
        ('SALES_ORDER', 'Sales Order Approval'),
        ('EXPENSE', 'Expense Claim Approval'),
        ('LEAVE', 'Employee Leave Approval'),
        ('DISCOUNT', 'Special Discount Approval'),
        ('PAYROLL', 'Payroll Run Approval'),
        ('INVOICE', 'Invoice Write-off Approval'),
    ]

    name = models.CharField(max_length=150)
    module_type = models.CharField(max_length=50, choices=MODULE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    auto_escalate_hours = models.PositiveIntegerField(default=48)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_module_type_display()})"

class WorkflowStage(models.Model):
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='stages')
    step_number = models.PositiveSmallIntegerField(default=1)
    name = models.CharField(max_length=100) # e.g. "Department Manager", "Finance Director"
    required_role = models.CharField(max_length=50, blank=True, null=True)
    specific_approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    threshold_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    can_auto_approve = models.BooleanField(default=False)

    class Meta:
        ordering = ['step_number']
        unique_together = ('workflow', 'step_number')

    def __str__(self):
        return f"{self.workflow.name} - Step {self.step_number}: {self.name}"

class WorkflowInstance(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.PROTECT, related_name='instances')
    current_stage = models.ForeignKey(WorkflowStage, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Generic relation to any model (PO, SalesOrder, LeaveRequest, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_workflows')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"WF #{self.id} - {self.workflow.name} - {self.status}"

class ApprovalAction(models.Model):
    ACTION_CHOICES = [
        ('APPROVE', 'Approved'),
        ('REJECT', 'Rejected'),
        ('ESCALATE', 'Escalated'),
        ('DELEGATE', 'Delegated'),
    ]

    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='actions')
    stage = models.ForeignKey(WorkflowStage, on_delete=models.SET_NULL, null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.actor} - {self.action} on WF #{self.instance.id} at {self.timestamp}"
