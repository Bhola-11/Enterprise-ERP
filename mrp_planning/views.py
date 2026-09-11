from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q

from .models import MasterProductionSchedule, SafetyStockRule, MRPRun, MRPRequirementItem
from .forms import MasterProductionScheduleForm, SafetyStockRuleForm, MRPExecutionForm
from .services import MRPCalculationEngine


@login_required
def mrp_dashboard(request):
    total_mps = MasterProductionSchedule.objects.count()
    active_mrp_runs = MRPRun.objects.count()
    total_planned_orders = MRPRequirementItem.objects.filter(status='RECOMMENDED').count()
    safety_stock_alerts = SafetyStockRule.objects.filter(is_active=True).count()

    recent_runs = MRPRun.objects.select_related('executed_by').order_by('-created_at')[:6]
    pending_requirements = MRPRequirementItem.objects.filter(status='RECOMMENDED').select_related('product', 'mrp_run').order_by('requirement_date')[:10]

    context = {
        'total_mps': total_mps,
        'active_mrp_runs': active_mrp_runs,
        'total_planned_orders': total_planned_orders,
        'safety_stock_alerts': safety_stock_alerts,
        'recent_runs': recent_runs,
        'pending_requirements': pending_requirements,
        'page_title': 'Material Requirements Planning (MRP II) Hub',
    }
    return render(request, 'mrp_planning/dashboard.html', context)


@login_required
def mps_list(request):
    schedules = MasterProductionSchedule.objects.select_related('product').order_by('-period_start')
    return render(request, 'mrp_planning/mps_list.html', {
        'schedules': schedules,
        'page_title': 'Master Production Schedule (MPS) Planner'
    })


@login_required
def mps_create(request):
    if request.method == 'POST':
        form = MasterProductionScheduleForm(request.POST)
        if form.is_valid():
            mps = form.save()
            messages.success(request, f"MPS planned for {mps.product.name} ({mps.period_start} to {mps.period_end}).")
            return redirect('mrp_planning:mps_list')
    else:
        form = MasterProductionScheduleForm(initial={
            'period_start': timezone.now().date(),
            'period_end': timezone.now().date() + timezone.timedelta(days=30),
            'planned_production_qty': Decimal('100.00'),
        })

    return render(request, 'mrp_planning/mps_form.html', {'form': form, 'page_title': 'Schedule Master Production (MPS)'})


@login_required
def run_mrp_wizard(request):
    if request.method == 'POST':
        form = MRPExecutionForm(request.POST)
        if form.is_valid():
            horizon = form.cleaned_data['planning_horizon_days']
            forecast = form.cleaned_data['include_forecast']
            safety = form.cleaned_data['include_safety_stock']

            run = MRPCalculationEngine.execute_mrp_run(
                planning_horizon_days=horizon,
                include_forecast=forecast,
                include_safety_stock=safety,
                user=request.user
            )
            messages.success(request, f"MRP Run #{run.run_number} computed {run.total_planned_orders_count} planned orders.")
            return redirect('mrp_planning:mrp_run_detail', pk=run.id)
    else:
        form = MRPExecutionForm()

    return render(request, 'mrp_planning/run_mrp_wizard.html', {'form': form, 'page_title': 'Execute MRP II Calculation Engine'})


@login_required
def mrp_run_detail(request, pk):
    run = get_object_or_404(MRPRun.objects.select_related('executed_by'), pk=pk)
    requirements = run.requirements.select_related('product').order_by('order_release_date')

    return render(request, 'mrp_planning/mrp_run_detail.html', {
        'run': run,
        'requirements': requirements,
        'page_title': f'MRP Results: {run.run_number}'
    })


@login_required
def safety_stock_list(request):
    rules = SafetyStockRule.objects.select_related('product', 'warehouse').all()
    return render(request, 'mrp_planning/safety_stock_list.html', {
        'rules': rules,
        'page_title': 'Safety Stock & Economic Order Quantity (EOQ)'
    })


@login_required
def safety_stock_create(request):
    if request.method == 'POST':
        form = SafetyStockRuleForm(request.POST)
        if form.is_valid():
            rule = form.save()
            messages.success(request, f"Safety stock rule set for {rule.product.sku}.")
            return redirect('mrp_planning:safety_stock_list')
    else:
        form = SafetyStockRuleForm()
    return render(request, 'mrp_planning/safety_stock_form.html', {'form': form, 'page_title': 'Set Safety Stock Rule'})
