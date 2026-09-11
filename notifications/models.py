from django.db import models
from django.conf import settings

class Notification(models.Model):
    CATEGORY_CHOICES = [
        ('SALES', 'Sales & Orders'),
        ('PURCHASE', 'Purchasing & Procurement'),
        ('INVENTORY', 'Inventory & Stock Alerts'),
        ('APPROVAL', 'Workflow Approvals'),
        ('ACCOUNTING', 'Finance & Invoicing'),
        ('HR', 'HR & Payroll'),
        ('SUPPORT', 'Support & Tickets'),
        ('SYSTEM', 'System Alert'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='SYSTEM')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL')
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"

def notify_user(recipient, title, message, category='SYSTEM', priority='NORMAL', link=None):
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        category=category,
        priority=priority,
        link=link
    )
