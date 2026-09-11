import uuid
import hmac
import hashlib
import json
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

class WebhookEndpoint(models.Model):
    name = models.CharField(max_length=200)
    target_url = models.URLField(max_length=500)
    secret_key = models.CharField(max_length=128, help_text="Shared HMAC secret key for signing payload digests")
    subscribed_events = models.JSONField(default=list, help_text="List of event topics: e.g. ['sales.order.created', 'inventory.stock.low']")
    is_active = models.BooleanField(default=True)
    retry_limit = models.PositiveIntegerField(default=5)
    total_deliveries_count = models.PositiveBigIntegerField(default=0)
    successful_deliveries_count = models.PositiveBigIntegerField(default=0)
    failed_deliveries_count = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Webhook Endpoint Subscription'
        verbose_name_plural = 'Webhook Endpoint Subscriptions'

    def __str__(self):
        return f"{self.name} -> {self.target_url}"

    @property
    def success_rate(self):
        if self.total_deliveries_count == 0:
            return 100.0
        return round((self.successful_deliveries_count / self.total_deliveries_count) * 100.0, 1)


class WebhookEvent(models.Model):
    event_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    topic = models.CharField(max_length=100, db_index=True) # e.g. sales.order.created
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Webhook Event'
        verbose_name_plural = 'Webhook Events'

    def __str__(self):
        return f"Event {self.event_id} [{self.topic}]"


class WebhookDeliveryAttempt(models.Model):
    STATUS_CHOICES = [
        ('DELIVERED', 'Delivered (2xx Success)'),
        ('FAILED', 'Delivery Failed (4xx/5xx/Timeout)'),
        ('RETRYING', 'Queued for Backoff Retry'),
    ]
    event = models.ForeignKey(WebhookEvent, on_delete=models.CASCADE, related_name='delivery_attempts')
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name='delivery_attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DELIVERED')
    http_status_code = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    attempt_number = models.PositiveIntegerField(default=1)
    duration_ms = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    signature_header = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Webhook Delivery Attempt'
        verbose_name_plural = 'Webhook Delivery Attempts'

    def __str__(self):
        return f"{self.event.topic} -> {self.endpoint.name}: {self.status} ({self.http_status_code})"