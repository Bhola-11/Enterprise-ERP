import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum

from .models import WebhookEndpoint, WebhookEvent, WebhookDeliveryAttempt
from .forms import WebhookEndpointForm, TestWebhookTriggerForm
from .services import WebhookDispatcher, HMACSignatureEngine


@login_required
def webhook_dashboard(request):
    total_endpoints = WebhookEndpoint.objects.count()
    active_endpoints = WebhookEndpoint.objects.filter(is_active=True).count()
    total_events = WebhookEvent.objects.count()
    total_deliveries = WebhookDeliveryAttempt.objects.count()
    successful_deliveries = WebhookDeliveryAttempt.objects.filter(status='DELIVERED').count()

    overall_rate = round((successful_deliveries / total_deliveries * 100.0), 1) if total_deliveries > 0 else 100.0

    recent_attempts = WebhookDeliveryAttempt.objects.select_related('event', 'endpoint').order_by('-created_at')[:10]
    endpoints = WebhookEndpoint.objects.order_by('-created_at')[:5]

    if request.method == 'POST':
        test_form = TestWebhookTriggerForm(request.POST)
        if test_form.is_valid():
            topic = test_form.cleaned_data['topic']
            payload_raw = test_form.cleaned_data['sample_payload']
            try:
                payload_dict = json.loads(payload_raw)
                event, attempts = WebhookDispatcher.trigger_event(topic, payload_dict)
                messages.success(request, f"Simulated Webhook '{topic}' triggered. Dispatched to {len(attempts)} endpoint(s).")
                return redirect('webhooks_engine:dashboard')
            except Exception as e:
                messages.error(request, f"Invalid JSON payload: {str(e)}")
    else:
        test_form = TestWebhookTriggerForm()

    context = {
        'total_endpoints': total_endpoints,
        'active_endpoints': active_endpoints,
        'total_events': total_events,
        'total_deliveries': total_deliveries,
        'successful_deliveries': successful_deliveries,
        'overall_rate': overall_rate,
        'recent_attempts': recent_attempts,
        'endpoints': endpoints,
        'test_form': test_form,
        'page_title': 'Enterprise Webhooks & Event Streams Hub'
    }
    return render(request, 'webhooks_engine/dashboard.html', context)


@login_required
def endpoint_list(request):
    endpoints = WebhookEndpoint.objects.all()
    return render(request, 'webhooks_engine/endpoint_list.html', {
        'endpoints': endpoints,
        'page_title': 'Webhook Subscriptions & Endpoints'
    })


@login_required
def endpoint_create(request):
    if request.method == 'POST':
        form = WebhookEndpointForm(request.POST)
        if form.is_valid():
            ep = form.save()
            messages.success(request, f"Webhook endpoint '{ep.name}' registered.")
            return redirect('webhooks_engine:endpoint_detail', pk=ep.id)
    else:
        form = WebhookEndpointForm()
    return render(request, 'webhooks_engine/endpoint_form.html', {'form': form, 'page_title': 'Register Webhook Endpoint'})


@login_required
def endpoint_detail(request, pk):
    endpoint = get_object_or_404(WebhookEndpoint, pk=pk)
    attempts = endpoint.delivery_attempts.select_related('event').order_by('-created_at')[:50]
    return render(request, 'webhooks_engine/endpoint_detail.html', {
        'endpoint': endpoint,
        'attempts': attempts,
        'page_title': f"Endpoint: {endpoint.name}"
    })


@login_required
def delivery_list(request):
    attempts = WebhookDeliveryAttempt.objects.select_related('event', 'endpoint').order_by('-created_at')[:150]
    return render(request, 'webhooks_engine/delivery_list.html', {
        'attempts': attempts,
        'page_title': 'Webhook Delivery Attempts & Audit Trail'
    })


@login_required
def delivery_retry(request, pk):
    attempt = get_object_or_404(WebhookDeliveryAttempt, pk=pk)
    if request.method == 'POST':
        new_attempt = WebhookDispatcher.redeliver_attempt(attempt.id)
        if new_attempt:
            messages.success(request, f"Redelivery completed for event {attempt.event.topic} -> Status: {new_attempt.status} ({new_attempt.http_status_code})")
        else:
            messages.error(request, "Failed to redeliver attempt.")
    return redirect('webhooks_engine:delivery_list')