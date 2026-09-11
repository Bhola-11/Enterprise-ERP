import time
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg, Q
from inventory.models import Product
from sales.models import SalesOrder

from .models import APIClient, APIKey, RateLimitPolicy, APIGatewayRequestLog
from .forms import APIClientForm, RateLimitPolicyForm, APIKeyGenerationForm
from .services import APIKeyManager, RateLimiterService, GatewayTelemetryService


@login_required
def gateway_dashboard(request):
    total_clients = APIClient.objects.count()
    active_keys = APIKey.objects.filter(is_revoked=False).count()
    total_requests = APIGatewayRequestLog.objects.count()
    avg_latency = APIGatewayRequestLog.objects.aggregate(a=Avg('response_time_ms'))['a'] or Decimal('0.00')

    success_requests = APIGatewayRequestLog.objects.filter(status_code__gte=200, status_code__lt=300).count()
    client_error_requests = APIGatewayRequestLog.objects.filter(status_code__gte=400, status_code__lt=500).count()
    server_error_requests = APIGatewayRequestLog.objects.filter(status_code__gte=500).count()

    recent_logs = APIGatewayRequestLog.objects.order_by('-timestamp')[:12]
    clients = APIClient.objects.annotate(keys_count=Count('api_keys')).order_by('-created_at')[:5]

    context = {
        'total_clients': total_clients,
        'active_keys': active_keys,
        'total_requests': total_requests,
        'avg_latency': round(avg_latency, 2),
        'success_requests': success_requests,
        'client_error_requests': client_error_requests,
        'server_error_requests': server_error_requests,
        'recent_logs': recent_logs,
        'clients': clients,
        'page_title': 'Enterprise API Gateway & Developer Hub'
    }
    return render(request, 'api_gateway/dashboard.html', context)


@login_required
def client_list(request):
    clients = APIClient.objects.select_related('organization', 'rate_limit_policy').annotate(keys_count=Count('api_keys')).all()
    return render(request, 'api_gateway/client_list.html', {
        'clients': clients,
        'page_title': 'Registered API Clients & Integrations'
    })


@login_required
def client_create(request):
    if request.method == 'POST':
        form = APIClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"API Client '{client.client_name}' registered successfully.")
            return redirect('api_gateway:client_detail', pk=client.id)
    else:
        form = APIClientForm()
    return render(request, 'api_gateway/client_form.html', {'form': form, 'page_title': 'Register API Client Application'})


@login_required
def client_detail(request, pk):
    client = get_object_or_404(APIClient.objects.select_related('organization', 'rate_limit_policy'), pk=pk)
    keys = client.api_keys.order_by('-created_at')
    new_key_raw = request.session.pop('new_key_raw', None)

    if request.method == 'POST':
        key_form = APIKeyGenerationForm(request.POST)
        if key_form.is_valid():
            name = key_form.cleaned_data['name']
            ktype = key_form.cleaned_data['key_type']
            exp = key_form.cleaned_data['expires_in_days']
            key_obj, raw_key = APIKeyManager.generate_api_key(client, name=name, key_type=ktype, expires_in_days=exp)
            request.session['new_key_raw'] = raw_key
            messages.success(request, f"New {ktype} API Key generated. Copy the secret now!")
            return redirect('api_gateway:client_detail', pk=client.id)
    else:
        key_form = APIKeyGenerationForm()

    return render(request, 'api_gateway/client_detail.html', {
        'client': client,
        'keys': keys,
        'key_form': key_form,
        'new_key_raw': new_key_raw,
        'page_title': f"Client: {client.client_name}"
    })


@login_required
def key_revoke(request, pk):
    key = get_object_or_404(APIKey, pk=pk)
    client_id = key.client.id
    if request.method == 'POST':
        APIKeyManager.revoke_key(key.id)
        messages.warning(request, f"API Key '{key.name}' ({key.raw_key_preview}) has been revoked.")
    return redirect('api_gateway:client_detail', pk=client_id)


@login_required
def policy_list(request):
    policies = RateLimitPolicy.objects.annotate(clients_count=Count('apiclient')).all()
    if request.method == 'POST':
        form = RateLimitPolicyForm(request.POST)
        if form.is_valid():
            p = form.save()
            messages.success(request, f"Rate limit policy '{p.name}' created.")
            return redirect('api_gateway:policy_list')
    else:
        form = RateLimitPolicyForm()

    return render(request, 'api_gateway/policy_list.html', {
        'policies': policies,
        'form': form,
        'page_title': 'Rate Limiting & Throttling Policies'
    })


@login_required
def log_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    logs = APIGatewayRequestLog.objects.select_related('api_key').all()

    if query:
        logs = logs.filter(Q(endpoint__icontains=query) | Q(client_name__icontains=query) | Q(client_ip__icontains=query))
    if status_filter:
        logs = logs.filter(status_code=int(status_filter))

    return render(request, 'api_gateway/log_viewer.html', {
        'logs': logs[:200],
        'query': query,
        'status_filter': status_filter,
        'page_title': 'Gateway Access & Security Audit Logs'
    })


# -----------------------------------------------------------------
# Gateway REST API Endpoints (External Consumers)
# -----------------------------------------------------------------

@csrf_exempt
def api_v1_gateway_ping(request):
    start_t = time.time()
    raw_key = request.headers.get('X-Nexora-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()

    key_obj = APIKeyManager.verify_key(raw_key) if raw_key else None
    duration_ms = (time.time() - start_t) * 1000

    GatewayTelemetryService.log_request(
        api_key=key_obj,
        endpoint=request.path,
        method=request.method,
        status_code=200,
        response_time_ms=duration_ms,
        client_ip=client_ip,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        headers={'auth_present': bool(raw_key)},
        query_params=dict(request.GET.items())
    )

    return JsonResponse({
        'status': 'ok',
        'gateway': 'Nexora Enterprise OS API Gateway v2.4',
        'authenticated': bool(key_obj),
        'client': key_obj.client.client_name if key_obj else 'Anonymous Guest',
        'timestamp': timezone.now().isoformat(),
    })


@csrf_exempt
def api_v1_inventory_catalog(request):
    start_t = time.time()
    raw_key = request.headers.get('X-Nexora-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()

    key_obj = APIKeyManager.verify_key(raw_key)
    if not key_obj:
        duration_ms = (time.time() - start_t) * 1000
        GatewayTelemetryService.log_request(None, request.path, request.method, 401, duration_ms, client_ip, request.META.get('HTTP_USER_AGENT', ''))
        return JsonResponse({'error': 'Unauthorized: Valid API Key required in X-Nexora-API-Key or Authorization header'}, status=401)

    # Check Rate Limit
    allowed, current_rpm, max_rpm = RateLimiterService.check_rate_limit(key_obj, client_ip)
    if not allowed:
        duration_ms = (time.time() - start_t) * 1000
        GatewayTelemetryService.log_request(key_obj, request.path, request.method, 429, duration_ms, client_ip, request.META.get('HTTP_USER_AGENT', ''))
        return JsonResponse({'error': f'Too Many Requests: RPM rate limit of {max_rpm} exceeded.', 'current_rpm': current_rpm}, status=429)

    products = Product.objects.filter(is_active=True).values('id', 'name', 'sku', 'cost_price', 'selling_price', 'current_stock')[:100]
    duration_ms = (time.time() - start_t) * 1000

    GatewayTelemetryService.log_request(key_obj, request.path, request.method, 200, duration_ms, client_ip, request.META.get('HTTP_USER_AGENT', ''))
    return JsonResponse({
        'status': 'success',
        'count': len(products),
        'rate_limit': {'current_rpm': current_rpm, 'max_rpm': max_rpm},
        'data': list(products)
    })


@csrf_exempt
def api_v1_orders_summary(request):
    start_t = time.time()
    raw_key = request.headers.get('X-Nexora-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()

    key_obj = APIKeyManager.verify_key(raw_key)
    if not key_obj:
        duration_ms = (time.time() - start_t) * 1000
        GatewayTelemetryService.log_request(None, request.path, request.method, 401, duration_ms, client_ip, request.META.get('HTTP_USER_AGENT', ''))
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    orders = SalesOrder.objects.select_related('customer').order_by('-order_date')[:50]
    data = [{
        'order_number': o.order_number,
        'customer': o.customer.name,
        'date': o.order_date.isoformat(),
        'total_amount': str(o.total_amount),
        'status': o.status
    } for o in orders]

    duration_ms = (time.time() - start_t) * 1000
    GatewayTelemetryService.log_request(key_obj, request.path, request.method, 200, duration_ms, client_ip, request.META.get('HTTP_USER_AGENT', ''))

    return JsonResponse({
        'status': 'success',
        'orders_count': len(data),
        'data': data
    })