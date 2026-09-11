from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q

from .models import DepreciableAsset, AssetDepreciationPeriod, AssetImpairmentRecord, AssetDisposalRecord
from .forms import DepreciableAssetForm, AssetImpairmentForm, AssetDisposalForm
from .services import DepreciationEngine, AssetImpairmentService, AssetDisposalService


@login_required
def assets_dashboard(request):
    total_assets = DepreciableAsset.objects.count()
    active_assets = DepreciableAsset.objects.filter(status='ACTIVE').count()
    
    cost_agg = DepreciableAsset.objects.aggregate(
        total_cost=Sum('acquisition_cost'),
        total_accum=Sum('accumulated_depreciation'),
        total_nbv=Sum('net_book_value')
    )
    total_cost = cost_agg['total_cost'] or Decimal('0.00')
    total_accum = cost_agg['total_accum'] or Decimal('0.00')
    total_nbv = cost_agg['total_nbv'] or Decimal('0.00')

    recent_assets = DepreciableAsset.objects.all()[:8]
    pending_depr_periods = AssetDepreciationPeriod.objects.filter(is_posted=False).select_related('asset').order_by('period_date')[:6]
    recent_impairments = AssetImpairmentRecord.objects.select_related('asset').all()[:5]
    recent_disposals = AssetDisposalRecord.objects.select_related('asset').all()[:5]

    context = {
        'total_assets': total_assets,
        'active_assets': active_assets,
        'total_cost': total_cost,
        'total_accum': total_accum,
        'total_nbv': total_nbv,
        'recent_assets': recent_assets,
        'pending_depr_periods': pending_depr_periods,
        'recent_impairments': recent_impairments,
        'recent_disposals': recent_disposals,
        'page_title': 'Fixed Assets & Depreciation Management'
    }
    return render(request, 'fixed_assets_depr/dashboard.html', context)


@login_required
def asset_list(request):
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('q', '')

    assets = DepreciableAsset.objects.all()

    if status_filter:
        assets = assets.filter(status=status_filter)
    if category_filter:
        assets = assets.filter(category_name__icontains=category_filter)
    if search_query:
        assets = assets.filter(
            Q(asset_tag__icontains=search_query) |
            Q(asset_name__icontains=search_query) |
            Q(location_facility__icontains=search_query)
        )

    categories = DepreciableAsset.objects.values_list('category_name', flat=True).distinct()

    context = {
        'assets': assets,
        'categories': categories,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'page_title': 'Fixed Asset Register (IAS 16 / MACRS)'
    }
    return render(request, 'fixed_assets_depr/asset_list.html', context)


@login_required
def asset_create(request):
    if request.method == 'POST':
        form = DepreciableAssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.net_book_value = asset.acquisition_cost
            asset.accumulated_depreciation = Decimal('0.00')
            asset.save()
            DepreciationEngine.generate_full_schedule(asset)
            messages.success(request, f"Fixed Asset '{asset.asset_tag}: {asset.asset_name}' registered and depreciation schedule generated.")
            return redirect('fixed_assets_depr:asset_detail', pk=asset.id)
    else:
        form = DepreciableAssetForm()

    return render(request, 'fixed_assets_depr/asset_form.html', {
        'form': form,
        'page_title': 'Register New Capital Asset'
    })


@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(DepreciableAsset, pk=pk)
    schedule = asset.depreciation_schedule.all()
    impairments = asset.impairments.all()
    disposals = asset.disposals.all()

    posted_count = schedule.filter(is_posted=True).count()
    unposted_count = schedule.filter(is_posted=False).count()

    context = {
        'asset': asset,
        'schedule': schedule,
        'impairments': impairments,
        'disposals': disposals,
        'posted_count': posted_count,
        'unposted_count': unposted_count,
        'page_title': f"Asset Detail: {asset.asset_tag} - {asset.asset_name}"
    }
    return render(request, 'fixed_assets_depr/asset_detail.html', context)


@login_required
def asset_post_depreciation(request, pk, period_id):
    asset = get_object_or_404(DepreciableAsset, pk=pk)
    period = get_object_or_404(AssetDepreciationPeriod, pk=period_id, asset=asset)

    if request.method == 'POST':
        if not period.is_posted:
            je = DepreciationEngine.post_depreciation_period(period, user=request.user)
            messages.success(request, f"Posted depreciation period {period.period_date} (${period.depreciation_amount}) with Journal Entry {je.entry_number if je else 'N/A'}.")
        else:
            messages.warning(request, "This depreciation period is already posted.")

    return redirect('fixed_assets_depr:asset_detail', pk=asset.id)


@login_required
def impairment_create(request, pk):
    asset = get_object_or_404(DepreciableAsset, pk=pk)
    if request.method == 'POST':
        form = AssetImpairmentForm(request.POST)
        if form.is_valid():
            rec_amt = form.cleaned_data['recoverable_amount']
            reason = form.cleaned_data['reason']
            imp = AssetImpairmentService.record_impairment(asset, rec_amt, reason, user=request.user)
            messages.success(request, f"IAS 36 Impairment recorded. Loss of ${imp.impairment_loss} posted to GL.")
            return redirect('fixed_assets_depr:asset_detail', pk=asset.id)
    else:
        form = AssetImpairmentForm(initial={'recoverable_amount': asset.net_book_value})

    return render(request, 'fixed_assets_depr/impairment_form.html', {
        'asset': asset,
        'form': form,
        'page_title': f"Record IAS 36 Impairment: {asset.asset_tag}"
    })


@login_required
def disposal_create(request, pk):
    asset = get_object_or_404(DepreciableAsset, pk=pk)
    if request.method == 'POST':
        form = AssetDisposalForm(request.POST)
        if form.is_valid():
            proceeds = form.cleaned_data['sale_proceeds']
            buyer = form.cleaned_data['buyer_name']
            disp = AssetDisposalService.record_disposal(asset, proceeds, buyer, user=request.user)
            outcome = "Gain" if disp.gain_loss_amount >= 0 else "Loss"
            messages.success(request, f"Asset Derecognized & Disposed. {outcome} of ${abs(disp.gain_loss_amount)} recorded.")
            return redirect('fixed_assets_depr:asset_detail', pk=asset.id)
    else:
        form = AssetDisposalForm()

    return render(request, 'fixed_assets_depr/disposal_form.html', {
        'asset': asset,
        'form': form,
        'page_title': f"Asset Derecognition & Disposal: {asset.asset_tag}"
    })

