from django.db import models
from django.conf import settings
from sales.models import Customer

class TicketCategory(models.Model):
    name = models.CharField(max_length=100) # Technical Support, Billing Inquiry, Feature Request
    sla_response_hours = models.PositiveSmallIntegerField(default=4)
    sla_resolution_hours = models.PositiveSmallIntegerField(default=24)

    class Meta:
        verbose_name_plural = 'Ticket Categories'

    def __str__(self):
        return self.name

class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open / New'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING', 'Waiting on Customer'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent / Critical'),
    ]

    ticket_id = models.CharField(max_length=30, unique=True) # e.g. TIK-2026-1001
    subject = models.CharField(max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='support_tickets')
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT, related_name='tickets')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"[{self.ticket_id}] {self.subject} ({self.get_status_display()})"

class TicketComment(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    is_internal_note = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        note_str = " (Internal Note)" if self.is_internal_note else ""
        return f"Comment on {self.ticket.ticket_id} by {self.author}{note_str}"
