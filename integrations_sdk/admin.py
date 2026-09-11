from django.contrib import admin
from .models import IntegrationConnector, EntitySyncMapping, IntegrationSyncLog

@admin.register(IntegrationConnector)
class IntegrationConnectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'connector_type', 'auth_type', 'sync_status', 'last_sync_at', 'is_active')
    list_filter = ('connector_type', 'sync_status', 'is_active')

@admin.register(EntitySyncMapping)
class EntitySyncMappingAdmin(admin.ModelAdmin):
    list_display = ('connector', 'entity_type', 'local_id', 'external_reference_id', 'sync_direction', 'last_sync_timestamp')
    list_filter = ('entity_type', 'sync_direction')
    search_fields = ('external_reference_id',)

@admin.register(IntegrationSyncLog)
class IntegrationSyncLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'connector', 'sync_type', 'records_processed', 'status', 'duration_seconds')
    list_filter = ('status', 'sync_type')