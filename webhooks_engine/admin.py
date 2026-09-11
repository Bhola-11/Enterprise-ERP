from django.contrib import admin
from .models import WebhookEndpoint, WebhookEvent, WebhookDeliveryAttempt

@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_url', 'is_active', 'total_deliveries_count', 'successful_deliveries_count', 'created_at')
    list_filter = ('is_active',)

@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'topic', 'created_at')
    search_fields = ('topic', 'event_id')

@admin.register(WebhookDeliveryAttempt)
class WebhookDeliveryAttemptAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event', 'endpoint', 'status', 'http_status_code', 'duration_ms', 'attempt_number')
    list_filter = ('status', 'http_status_code')