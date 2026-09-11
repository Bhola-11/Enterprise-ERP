import uuid
import secrets
import hashlib
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from organizations.models import Organization

class RateLimitPolicy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    requests_per_minute = models.PositiveIntegerField(default=60)
    requests_per_hour = models.PositiveIntegerField(default=1000)
    burst_limit = models.PositiveIntegerField(default=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rate Limit Policy'
        verbose_name_plural = 'Rate Limit Policies'

    def __str__(self):
        return f"{self.name} ({self.requests_per_minute} req/min, {self.requests_per_hour} req/hr)"


class APIClient(models.Model):
    client_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    client_name = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='api_clients', null=True, blank=True)
    contact_email = models.EmailField()
    rate_limit_policy = models.ForeignKey(RateLimitPolicy, on_delete=models.SET_NULL, null=True, blank=True)
    ip_whitelist = models.TextField(blank=True, help_text="Comma-separated IPv4/IPv6 addresses or CIDRs. Leave blank for unrestricted.")
    allowed_scopes = models.CharField(max_length=255, default='read:inventory,read:sales,write:orders', help_text="Comma-separated scopes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['client_name']
        verbose_name = 'API Client'
        verbose_name_plural = 'API Clients'

    def __str__(self):
        return f"{self.client_name} ({self.client_id})"


class APIKey(models.Model):
    KEY_TYPES = [
        ('LIVE', 'Production / Live (nx_live_)'),
        ('TEST', 'Sandbox / Testing (nx_test_)'),
    ]
    client = models.ForeignKey(APIClient, on_delete=models.CASCADE, related_name='api_keys')
    key_type = models.CharField(max_length=10, choices=KEY_TYPES, default='LIVE')
    name = models.CharField(max_length=150, default='Default Integration Key')
    key_prefix = models.CharField(max_length=20) # e.g. nx_live_
    key_hash = models.CharField(max_length=128, unique=True, db_index=True) # SHA-256
    raw_key_preview = models.CharField(max_length=40) # e.g. nx_live_...9f4a
    is_revoked = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    total_calls_count = models.PositiveBigIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'

    def __str__(self):
        return f"{self.name} [{self.raw_key_preview}] - {self.client.client_name}"

    @property
    def is_valid(self):
        if self.is_revoked:
            return False
        if not self.client.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class APIGatewayRequestLog(models.Model):
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, blank=True, related_name='request_logs')
    client_name = models.CharField(max_length=200, blank=True)
    endpoint = models.CharField(max_length=255, db_index=True)
    http_method = models.CharField(max_length=10)
    status_code = models.PositiveIntegerField(db_index=True)
    response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    request_headers = models.JSONField(default=dict, blank=True)
    query_params = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'API Request Log'
        verbose_name_plural = 'API Request Logs'

    def __str__(self):
        return f"{self.http_method} {self.endpoint} -> {self.status_code} ({self.response_time_ms}ms)"