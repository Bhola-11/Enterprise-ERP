from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum

from .models import CashPoolHeader, CashPoolParticipant, CashSweepingExecution, LiquidityForecast, FXHedgingContract
from .forms import CashPoolHeaderForm, CashPoolParticipantForm, FXHedgingContractForm
from .services import CashSweepingEngine, LiquidityForecastingService


@login_required
def treasury_dashboard(request):
    total_pools = CashPoolHeader.objects.count()
    active_pools = CashPoolHeader.objects.filter(is_active=True).count()
    total_swept = CashSweepingExecution.objects.aggregate(s=Sum('total_swept_in'))['s'] or Decimal('0.00')

    latest_forecast = LiquidityForecast.objects.order_by('-created_at').first()
    active_hedges = FXHedgingContract.objects.filter(status='ACTIVE')
    hedging_notional = active_hedges.aggregate(s=Sum('notional_amount'))['s'] or Decimal('0.00')

    pools = CashPoolHeader.objects.select_related('pool_leader_bank').annotate(parts_count=Count('participants')).all()
    recent_sweeps = CashSweepingExecution.objects.select_related('pool').order_by('-created_at')[:6]

    context = {
        'total_pools': total_pools,
        'active_pools': active_pools,
        'total_swept': total_swept,
        'latest_forecast': latest_forecast,
        'hedging_notional': hedging_notional,
        'pools': pools,
        'recent_sweeps': recent_sweeps,
        'page_title': 'Corporate Treasury & Cash Concentration Hub'
    }
    return render(request, 'treasury_cash/dashboard.html', context)


@login_required
def pool_list(request):
    pools = CashPoolHeader.objects.select_related('pool_leader_bank').annotate(parts_count=Count('participants')).all()
    return render(request, 'treasury_cash/pool_list.html', {
        'pools': pools,
        'page_title': 'Cash Concentration & Sweeping Pools'
    })


@login_required
def pool_create(request):
    if request.method == 'POST':
        form = CashPoolHeaderForm(request.POST)
        if form.is_valid():
            p = form.save()
            messages.success(request, f"Cash Pool '{p.name}' created.")
            return redirect('treasury_cash:pool_detail', pk=p.id)
    else:
        form = CashPoolHeaderForm()
    return render(request, 'treasury_cash/pool_form.html', {'form': form, 'page_title': 'Create Cash Pool'})


@login_required
def pool_detail(request, pk):
    pool = get_object_or_404(CashPoolHeader.objects.select_related('pool_leader_bank'), pk=pk)
    participants = pool.participants.select_related('bank_account').all()
    executions = pool.sweeping_executions.order_by('-created_at')[:20]

    if request.method == 'POST':
        part_form = CashPoolParticipantForm(request.POST)
        if part_form.is_valid():
            part = part_form.save(commit=False)
            part.pool = pool
            part.save()
            messages.success(request, f"Added participant bank account {part.bank_account.bank_name}.")
            return redirect('treasury_cash:pool_detail', pk=pool.id)
    else:
        part_form = CashPoolParticipantForm()

    return render(request, 'treasury_cash/pool_detail.html', {
        'pool': pool,
        'participants': participants,
        'executions': executions,
        'part_form': part_form,
        'page_title': f"Pool: {pool.name}"
    })


@login_required
def pool_execute_sweep(request, pk):
    pool = get_object_or_404(CashPoolHeader, pk=pk)
    if request.method == 'POST':
        execution = CashSweepingEngine.execute_sweeping_run(pool, user=request.user)
        messages.success(request, f"Cash sweeping #{execution.execution_number} executed: Swept In ${execution.total_swept_in}, Swept Out ${execution.total_swept_out}.")
    return redirect('treasury_cash:pool_detail', pk=pool.id)


@login_required
def forecast_list(request):
    forecasts = LiquidityForecast.objects.order_by('-created_at')
    if request.method == 'POST':
        f = LiquidityForecastingService.generate_90day_forecast()
        messages.success(request, f"New rolling 90-day liquidity forecast generated.")
        return redirect('treasury_cash:forecast_list')

    return render(request, 'treasury_cash/forecast_list.html', {
        'forecasts': forecasts,
        'page_title': '90-Day Rolling Treasury Liquidity Forecasts'
    })


@login_required
def hedging_list(request):
    hedges = FXHedgingContract.objects.order_by('-maturity_date')
    if request.method == 'POST':
        form = FXHedgingContractForm(request.POST)
        if form.is_valid():
            h = form.save()
            messages.success(request, f"FX Hedging Contract #{h.contract_number} booked.")
            return redirect('treasury_cash:hedging_list')
    else:
        form = FXHedgingContractForm()

    return render(request, 'treasury_cash/hedging_list.html', {
        'hedges': hedges,
        'form': form,
        'page_title': 'FX Hedging & Derivative Contracts'
    })