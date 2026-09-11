from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import Asset, AssetCategory, AssetMaintenanceLog
from .forms import AssetForm
from audit.middleware import log_audit_event

@login_required
def asset_list(request):
    assets = Asset.objects.select_related('category', 'assigned_to').all()
    status_filter = request.GET.get('status')
    category_id = request.GET.get('category')
    search = request.GET.get('q')

    if status_filter:
        assets = assets.filter(status=status_filter)
    if category_id:
        assets = assets.filter(category_id=category_id)
    if search:
        assets = assets.filter(models.Q(name__icontains=search) | models.Q(asset_tag__icontains=search) | models.Q(serial_number__icontains=search))

    paginator = Paginator(assets, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    categories = AssetCategory.objects.all()

    total_cost = Asset.objects.aggregate(Sum('purchase_cost'))['purchase_cost__sum'] or 0
    total_val = Asset.objects.aggregate(Sum('current_value'))['current_value__sum'] or 0

    return render(request, 'assets/asset_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'statuses': Asset.STATUS_CHOICES,
        'selected_status': status_filter,
        'selected_category': category_id,
        'total_cost': total_cost,
        'total_val': total_val,
    })

@login_required
def asset_create(request):
    form = AssetForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ast = form.save()
        log_audit_event(request.user, 'CREATE', 'Asset', ast.id, str(ast), request=request)
        messages.success(request, f"Asset '{ast.name}' [{ast.asset_tag}] registered successfully!")
        return redirect('assets:list')
    return render(request, 'assets/asset_form.html', {'form': form, 'title': 'Register Asset'})

@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset.objects.select_related('category', 'assigned_to'), pk=pk)
    logs = asset.maintenance_logs.all()
    return render(request, 'assets/asset_detail.html', {'asset': asset, 'logs': logs})
