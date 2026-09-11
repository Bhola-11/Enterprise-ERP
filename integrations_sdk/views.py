from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count

from .models import IntegrationConnector, EntitySyncMapping, IntegrationSyncLog
from .forms import IntegrationConnectorForm
from .services import IntegrationSyncRunner


@login_required
def marketplace_dashboard(request):
    connectors = IntegrationConnector.objects.annotate(mappings_count=Count('mappings')).all()
    active_count = connectors.filter(is_active=True).count()
    total_mappings = EntitySyncMapping.objects.count()
    recent_logs = IntegrationSyncLog.objects.select_related('connector').order_by('-created_at')[:8]

    # Pre-canned Catalog App metadata
    catalog_templates = [
        {'type': 'STRIPE', 'name': 'Stripe Payments', 'desc': 'Automate customer card billing, ACH payments, and ledger entries.', 'icon': 'fa-brands fa-stripe', 'badge': 'Finance'},
        {'type': 'SALESFORCE', 'name': 'Salesforce CRM', 'desc': 'Two-way synchronization for Leads, Contacts, and Opportunities.', 'icon': 'fa-brands fa-salesforce', 'badge': 'CRM'},
        {'type': 'FEDEX', 'name': 'FedEx Freight Bridge', 'desc': 'Real-time airway bill generation and multi-modal shipment tracking.', 'icon': 'fa-solid fa-truck-fast', 'badge': 'Logistics'},
        {'type': 'SAP_BRIDGE', 'name': 'SAP ERP GL Bridge', 'desc': 'Double-entry General Ledger sync via SAP IDoc & RFC connectors.', 'icon': 'fa-solid fa-server', 'badge': 'Enterprise'},
        {'type': 'SHOPIFY', 'name': 'Shopify Commerce', 'desc': 'Direct e-commerce catalog publishing and sales order ingestion.', 'icon': 'fa-brands fa-shopify', 'badge': 'E-Commerce'},
    ]

    context = {
        'connectors': connectors,
        'active_count': active_count,
        'total_mappings': total_mappings,
        'recent_logs': recent_logs,
        'catalog_templates': catalog_templates,
        'page_title': 'Enterprise Integrations Marketplace & SDK Hub'
    }
    return render(request, 'integrations_sdk/marketplace.html', context)


@login_required
def connector_create(request):
    initial_type = request.GET.get('type', 'STRIPE')
    initial_name = dict(IntegrationConnector.CONNECTOR_TYPES).get(initial_type, 'New Integration')

    if request.method == 'POST':
        form = IntegrationConnectorForm(request.POST)
        if form.is_valid():
            conn = form.save()
            messages.success(request, f"Integration connector '{conn.name}' connected successfully.")
            return redirect('integrations_sdk:connector_detail', pk=conn.id)
    else:
        form = IntegrationConnectorForm(initial={'connector_type': initial_type, 'name': initial_name})

    return render(request, 'integrations_sdk/connector_form.html', {'form': form, 'page_title': 'Configure Integration Connector'})


@login_required
def connector_detail(request, pk):
    connector = get_object_or_404(IntegrationConnector, pk=pk)
    mappings = connector.mappings.order_by('-last_sync_timestamp')[:50]
    logs = connector.sync_logs.order_by('-created_at')[:20]

    return render(request, 'integrations_sdk/connector_detail.html', {
        'connector': connector,
        'mappings': mappings,
        'logs': logs,
        'page_title': f"Connector: {connector.name}"
    })


@login_required
def connector_trigger_sync(request, pk):
    connector = get_object_or_404(IntegrationConnector, pk=pk)
    if request.method == 'POST':
        log = IntegrationSyncRunner.execute_sync(connector, sync_type='MANUAL_TRIGGER')
        if log.status == 'SUCCESS':
            messages.success(request, f"Sync successful for {connector.name}: {log.records_processed} records mapped.")
        else:
            messages.error(request, f"Sync error: {log.log_details}")
    return redirect('integrations_sdk:connector_detail', pk=connector.id)


@login_required
def sync_log_list(request):
    logs = IntegrationSyncLog.objects.select_related('connector').order_by('-created_at')[:150]
    return render(request, 'integrations_sdk/sync_log_list.html', {
        'logs': logs,
        'page_title': 'Integration Sync Audit & Execution History'
    })