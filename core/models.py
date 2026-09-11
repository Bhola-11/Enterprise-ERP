from django.db import models

class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True, null=True)
    is_public = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} = {self.value[:30]}"

class IntegrationConfig(models.Model):
    name = models.CharField(max_length=100) # Stripe, SendGrid, Twilio, Slack, SAP Connector
    provider_code = models.CharField(max_length=50, unique=True)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    endpoint_url = models.URLField(blank=True, null=True)
    webhook_secret = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    extra_config = models.JSONField(default=dict, blank=True)

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({status})"
