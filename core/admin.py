from django.contrib import admin
from .models import SystemSetting, IntegrationConfig

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'is_public', 'updated_at')
    search_fields = ('key', 'value')

@admin.register(IntegrationConfig)
class IntegrationConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider_code', 'endpoint_url', 'is_active')
    list_filter = ('is_active',)
