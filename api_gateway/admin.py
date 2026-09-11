from django.contrib import admin
from .models import RateLimitPolicy, APIClient, APIKey, APIGatewayRequestLog

@admin.register(RateLimitPolicy)
class RateLimitPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'requests_per_minute', 'requests_per_hour', 'burst_limit', 'is_default')

@admin.register(APIClient)
class APIClientAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'client_id', 'contact_email', 'rate_limit_policy', 'is_active')
    search_fields = ('client_name', 'contact_email')

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'key_type', 'raw_key_preview', 'total_calls_count', 'is_revoked', 'last_used_at')
    list_filter = ('key_type', 'is_revoked')

@admin.register(APIGatewayRequestLog)
class APIGatewayRequestLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'http_method', 'endpoint', 'status_code', 'response_time_ms', 'client_name', 'client_ip')
    list_filter = ('http_method', 'status_code')
    search_fields = ('endpoint', 'client_name', 'client_ip')