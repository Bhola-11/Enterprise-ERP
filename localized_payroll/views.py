from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal

from .models import TaxJurisdictionRule, SalaryStructure, PayRunBatch, EmployeePayslip
from .forms import TaxJurisdictionRuleForm, SalaryStructureForm, PayRunLaunchForm
from .services import GrossToNetPayrollEngine
from hr.models import Employee


@login_required
def dashboard(request):
    total_runs = PayRunBatch.objects.count()
    latest_run = PayRunBatch.objects.order_by('-created_at').first()

    totals = PayRunBatch.objects.aggregate(
        gross=Sum('total_gross_disbursed'),
        tax=Sum('total_statutory_deductions'),
        net=Sum('total_net_disbursed')
    )
    ytd_gross = totals['gross'] or Decimal('0.00')
    ytd_tax = totals['tax'] or Decimal('0.00')
    ytd_net = totals['net'] or Decimal('0.00')

    active_salaries = SalaryStructure.objects.filter(is_active=True).count()
    jurisdictions = TaxJurisdictionRule.objects.filter(is_active=True)
    recent_runs = PayRunBatch.objects.all()[:6]

    context = {
        'total_runs': total_runs,
        'latest_run': latest_run,
        'ytd_gross': ytd_gross,
        'ytd_tax': ytd_tax,
        'ytd_net': ytd_net,
        'active_salaries': active_salaries,
        'jurisdictions': jurisdictions,
        'recent_runs': recent_runs,
        'page_title': 'Localized Multi-Jurisdiction Payroll Engine'
    }
    return render(request, 'localized_payroll/dashboard.html', context)


@login_required
def payrun_list(request):
    runs = PayRunBatch.objects.all()
    return render(request, 'localized_payroll/payrun_list.html', {
        'runs': runs,
        'page_title': 'Batch Pay Runs'
    })


@login_required
def payrun_create(request):
    now = timezone.now().date()
    if request.method == 'POST':
        form = PayRunLaunchForm(request.POST)
        if form.is_valid():
            m = form.cleaned_data['period_month']
            y = form.cleaned_data['period_year']
            p_date = form.cleaned_data['pay_date']
            batch = GrossToNetPayrollEngine.execute_batch_pay_run(m, y, p_date, user=request.user)
            messages.success(request, f"Pay Run #{batch.batch_number} computed. Net Disbursed: ${batch.total_net_disbursed:,.2f} across {batch.total_payslips_count} employees.")
            return redirect('localized_payroll:payrun_detail', pk=batch.id)
    else:
        form = PayRunLaunchForm(initial={
            'period_month': now.month,
            'period_year': now.year,
            'pay_date': now
        })

    return render(request, 'localized_payroll/payrun_form.html', {
        'form': form,
        'page_title': 'Execute New Gross-to-Net Pay Run'
    })


@login_required
def payrun_detail(request, pk):
    batch = get_object_or_404(PayRunBatch, pk=pk)
    payslips = batch.payslips.select_related('employee', 'employee__department').all()

    context = {
        'batch': batch,
        'payslips': payslips,
        'page_title': f"Pay Run Detail: #{batch.batch_number}"
    }
    return render(request, 'localized_payroll/payrun_detail.html', context)


@login_required
def payslip_detail(request, pk):
    payslip = get_object_or_404(EmployeePayslip, pk=pk)
    return render(request, 'localized_payroll/payslip_detail.html', {
        'payslip': payslip,
        'page_title': f"Payslip: {payslip.employee.first_name} {payslip.employee.last_name} ({payslip.pay_run.batch_number})"
    })


@login_required
def salary_list(request):
    salaries = SalaryStructure.objects.select_related('employee', 'jurisdiction', 'employee__department').all()
    return render(request, 'localized_payroll/salary_list.html', {
        'salaries': salaries,
        'page_title': 'Employee Salary Structures'
    })


@login_required
def salary_create(request):
    if request.method == 'POST':
        form = SalaryStructureForm(request.POST)
        if form.is_valid():
            s = form.save()
            messages.success(request, f"Salary Structure configured for {s.employee}.")
            return redirect('localized_payroll:salary_list')
    else:
        form = SalaryStructureForm()

    return render(request, 'localized_payroll/salary_form.html', {
        'form': form,
        'page_title': 'Configure Salary Structure'
    })


@login_required
def jurisdictions_list(request):
    rules = TaxJurisdictionRule.objects.all()
    return render(request, 'localized_payroll/jurisdictions_list.html', {
        'rules': rules,
        'page_title': 'Statutory Tax Jurisdictions & Rates'
    })
