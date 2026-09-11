from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum

from .models import ConsolidationGroup, CurrencyExchangeRate, InterCompanyEliminationRule, ConsolidatedStatement
from .forms import ConsolidationGroupForm, CurrencyExchangeRateForm, InterCompanyEliminationRuleForm, RunConsolidationForm
from .services import ConsolidationEngine


@login_required
def consolidation_dashboard(request):
    total_groups = ConsolidationGroup.objects.count()
    active_groups = ConsolidationGroup.objects.filter(is_active=True).count()
    total_statements = ConsolidatedStatement.objects.count()
    total_eliminations = ConsolidatedStatement.objects.aggregate(s=Sum('total_eliminations'))['s'] or Decimal('0.00')

    recent_statements = ConsolidatedStatement.objects.select_related('group').order_by('-created_at')[:8]
    groups = ConsolidationGroup.objects.annotate(statements_count=Count('statements')).all()
    exchange_rates = CurrencyExchangeRate.objects.order_by('-effective_date')[:6]

    context = {
        'total_groups': total_groups,
        'active_groups': active_groups,
        'total_statements': total_statements,
        'total_eliminations': total_eliminations,
        'recent_statements': recent_statements,
        'groups': groups,
        'exchange_rates': exchange_rates,
        'page_title': 'Multi-Entity Financial Consolidation & IAS 21 Hub'
    }
    return render(request, 'consolidation/dashboard.html', context)


@login_required
def group_list(request):
    groups = ConsolidationGroup.objects.annotate(statements_count=Count('statements')).all()
    return render(request, 'consolidation/group_list.html', {
        'groups': groups,
        'page_title': 'Consolidation Corporate Groups'
    })


@login_required
def group_create(request):
    if request.method == 'POST':
        form = ConsolidationGroupForm(request.POST)
        if form.is_valid():
            g = form.save()
            messages.success(request, f"Consolidation Group '{g.name}' created.")
            return redirect('consolidation:group_detail', pk=g.id)
    else:
        form = ConsolidationGroupForm()
    return render(request, 'consolidation/group_form.html', {'form': form, 'page_title': 'Create Consolidation Group'})


@login_required
def group_detail(request, pk):
    group = get_object_or_404(ConsolidationGroup.objects.prefetch_related('subsidiary_organizations'), pk=pk)
    rules = group.elimination_rules.all()
    statements = group.statements.order_by('-period_end')[:20]

    return render(request, 'consolidation/group_detail.html', {
        'group': group,
        'rules': rules,
        'statements': statements,
        'page_title': f"Group: {group.name}"
    })


@login_required
def run_consolidation_wizard(request):
    if request.method == 'POST':
        form = RunConsolidationForm(request.POST)
        if form.is_valid():
            grp = form.cleaned_data['group']
            stype = form.cleaned_data['statement_type']
            p_start = form.cleaned_data['period_start']
            p_end = form.cleaned_data['period_end']

            stmt = ConsolidationEngine.generate_consolidated_report(grp, stype, p_start, p_end, user=request.user)
            messages.success(request, f"Consolidated {stmt.get_statement_type_display()} #{stmt.statement_number} generated successfully.")
            return redirect('consolidation:statement_detail', pk=stmt.id)
    else:
        now = timezone.now().date()
        p_start = now.replace(month=1, day=1)
        p_end = now
        form = RunConsolidationForm(initial={'period_start': p_start, 'period_end': p_end})

    return render(request, 'consolidation/run_wizard.html', {'form': form, 'page_title': 'Generate Consolidated Financial Statements'})


@login_required
def statement_detail(request, pk):
    statement = get_object_or_404(ConsolidatedStatement.objects.select_related('group'), pk=pk)
    line_items = statement.statement_data.get('line_items', [])

    return render(request, 'consolidation/statement_detail.html', {
        'statement': statement,
        'line_items': line_items,
        'page_title': f"Consolidated Statement: {statement.statement_number}"
    })


@login_required
def rates_list(request):
    rates = CurrencyExchangeRate.objects.order_by('-effective_date')
    if request.method == 'POST':
        form = CurrencyExchangeRateForm(request.POST)
        if form.is_valid():
            r = form.save()
            messages.success(request, f"Exchange rate for {r.from_currency}/{r.to_currency} saved.")
            return redirect('consolidation:rates_list')
    else:
        form = CurrencyExchangeRateForm()

    return render(request, 'consolidation/rates_list.html', {
        'rates': rates,
        'form': form,
        'page_title': 'IAS 21 Foreign Exchange Rate Table'
    })