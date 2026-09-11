import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

class IntegrationConnector(models.Model):
    CONNECTOR_TYPES = [
        ('STRIPE', 'Stripe Billing & Global Payments Gateway'),
        ('SALESFORCE', 'Salesforce CRM Enterprise Synchronizer'),
        ('FEDEX', 'FedEx Logistics & Freight Carrier Bridge'),
        ('SAP_BRIDGE', 'SAP ERP & NetSuite General Ledger Bridge'),
        ('SHOPIFY', 'Shopify E-Commerce Storefront Connector'),
    ]
    AUTH_TYPES = [
        ('API_KEY', 'Bearer / API Secret Token'),
        ('OAUTH2', 'OAuth 2.0 PKCE / Authorization Code'),
        ('BASIC_AUTH', 'HTTP Basic Credentials'),
        ('WEBHOOK_SECRET', 'Cryptographic Webhook Secret'),
    ]
    SYNC_STATUSES = [
        ('IDLE', 'Idle / Ready'),
        ('RUNNING', 'Synchronization In-Progress'),
        ('SUCCESS', 'Healthy / Last Sync Succeeded'),
        ('ERROR', 'Error / Sync Failed'),
    ]

    name = models.CharField(max_length=200)
    connector_type = models.CharField(max_length=30, choices=CONNECTOR_TYPES)
    auth_type = models.CharField(max_length=30, choices=AUTH_TYPES, default='API_KEY')
    base_url = models.URLField(max_length=500, blank=True)
    credentials_config = models.JSONField(default=dict, blank=True, help_text="Encrypted/masked configuration dictionary")
    sync_interval_minutes = models.PositiveIntegerField(default=60)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUSES, default='IDLE')
    error_message = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Enterprise Integration Connector'
        verbose_name_plural = 'Enterprise Integration Connectors'

    def __str__(self):
        return f"{self.name} ({self.get_connector_type_display()}) [{self.sync_status}]"


class EntitySyncMapping(models.Model):
    ENTITY_TYPES = [
        ('CUSTOMER', 'Customer / Account Record'),
        ('PRODUCT', 'Inventory Product SKU'),
        ('SALES_ORDER', 'Sales Order Record'),
        ('INVOICE', 'Billing Invoice'),
        ('PAYMENT', 'Payment Settlement'),
        ('JOURNAL_ENTRY', 'GL Journal Entry'),
    ]
    SYNC_DIRECTIONS = [
        ('INBOUND', 'Inbound (External -> Nexora)'),
        ('OUTBOUND', 'Outbound (Nexora -> External)'),
        ('BIDIRECTIONAL', 'Bi-directional Two-Way Sync'),
    ]

    connector = models.ForeignKey(IntegrationConnector, on_delete=models.CASCADE, related_name='mappings')
    entity_type = models.CharField(max_length=30, choices=ENTITY_TYPES)
    local_id = models.PositiveIntegerField()
    external_reference_id = models.CharField(max_length=150, db_index=True)
    sync_direction = models.CharField(max_length=20, choices=SYNC_DIRECTIONS, default='BIDIRECTIONAL')
    last_sync_timestamp = models.DateTimeField(auto_now=True)
    sync_payload_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('connector', 'entity_type', 'local_id')
        ordering = ['-last_sync_timestamp']
        verbose_name = 'Entity Sync Mapping'
        verbose_name_plural = 'Entity Sync Mappings'

    def __str__(self):
        return f"{self.connector.name} | {self.entity_type} #{self.local_id} <-> {self.external_reference_id}"


class IntegrationSyncLog(models.Model):
    STATUS_CHOICES = [
        ('SUCCESS', 'Successful'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Completed with Warnings'),
    ]

    connector = models.ForeignKey(IntegrationConnector, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=50, default='MANUAL_TRIGGER')
    records_processed = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS')
    log_details = models.TextField(blank=True)
    duration_seconds = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Integration Sync Log'
        verbose_name_plural = 'Integration Sync Logs'

    def __str__(self):
        return f"{self.connector.name} Sync @ {self.created_at.strftime('%Y-%m-%d %H:%M')} [{self.status}]"