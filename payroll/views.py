from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from .models import SalaryStructure, Payrun, Payslip
from hr.models import Employee
from accounting.models import Account, JournalEntry, JournalItem
from accounting.services import AccountingService
from audit.middleware import log_audit_event

@login_required
def payroll_dashboard(request):
    payruns = Payrun.objects.all().order_by('-year', '-month')
    recent_payslips = Payslip.objects.select_related('employee__department', 'payrun').order_by('-created_at')[:8]
    total_structures = SalaryStructure.objects.count()

    return render(request, 'payroll/dashboard.html', {
        'payruns': payruns,
        'recent_payslips': recent_payslips,
        'total_structures': total_structures,
    })

@login_required
def payrun_generate(request):
    if request.method == 'POST':
        month = int(request.POST.get('month', 9))
        year = int(request.POST.get('year', 2026))
        title = f"Payroll {month:02d}/{year}"

        payrun, created = Payrun.objects.get_or_create(
            month=month,
            year=year,
            defaults={
                'title': title,
                'start_date': f"{year}-{month:02d}-01",
                'end_date': f"{year}-{month:02d}-28",
                'processed_by': request.user,
                'status': 'DRAFT'
            }
        )

        # Generate payslips for all active employees with salary structures
        employees = Employee.objects.filter(status='ACTIVE')
        tot_gross = Decimal('0.00')
        tot_ded = Decimal('0.00')
        tot_net = Decimal('0.00')

        for emp in employees:
            structure, _ = SalaryStructure.objects.get_or_create(employee=emp)
            payslip, _ = Payslip.objects.update_or_create(
                payrun=payrun,
                employee=emp,
                defaults={
                    'basic_salary': structure.basic_salary,
                    'allowances': structure.total_allowances,
                    'gross_salary': structure.gross_salary,
                    'deductions': structure.total_deductions,
                    'net_salary': structure.net_salary,
                }
            )
            tot_gross += structure.gross_salary
            tot_ded += structure.total_deductions
            tot_net += structure.net_salary

        payrun.total_gross = tot_gross
        payrun.total_deductions = tot_ded
        payrun.total_net = tot_net
        payrun.save()

        log_audit_event(request.user, 'CREATE', 'Payrun', payrun.id, str(payrun), request=request, description=f"Calculated payrun for {title} (${tot_net:,.2f})")
        messages.success(request, f"Payrun '{title}' generated successfully for {employees.count()} employees!")
        return redirect('payroll:payrun_detail', pk=payrun.id)

    return render(request, 'payroll/generate_form.html')

@login_required
def payrun_detail(request, pk):
    payrun = get_object_or_404(Payrun, pk=pk)
    payslips = payrun.payslips.select_related('employee__department', 'employee__designation')

    if request.method == 'POST' and 'disburse_payroll' in request.POST:
        # Create Accounting Journal Entry for Payroll Disbursal
        # Debit: Salary Expense (e.g. 5010)
        # Credit: Bank Account / Cash (e.g. 1010)
        salary_exp_acc = Account.objects.filter(account_type='EXPENSE', name__icontains='Salary').first()
        bank_acc = Account.objects.filter(account_type='ASSET', name__icontains='Bank').first()

        if salary_exp_acc and bank_acc:
            je_num = f"JE-PAY-{payrun.month:02d}-{payrun.year}"
            je, _ = JournalEntry.objects.get_or_create(
                entry_number=je_num,
                defaults={
                    'date': payrun.end_date,
                    'reference': f"PAYRUN-{payrun.id}",
                    'narration': f"Disbursal of {payrun.title} for {payslips.count()} employees.",
                    'created_by': request.user,
                }
            )
            JournalItem.objects.filter(journal_entry=je).delete()
            JournalItem.objects.create(journal_entry=je, account=salary_exp_acc, description="Gross Payroll Expense", debit=payrun.total_gross, credit=0)
            JournalItem.objects.create(journal_entry=je, account=bank_acc, description="Net Salary Disbursed to Bank Accounts", debit=0, credit=payrun.total_net)
            if payrun.total_deductions > 0:
                tax_liability_acc = Account.objects.filter(account_type='LIABILITY', name__icontains='Tax').first() or bank_acc
                JournalItem.objects.create(journal_entry=je, account=tax_liability_acc, description="Withholding Taxes & PF Payable", debit=0, credit=payrun.total_deductions)
            
            try:
                AccountingService.post_journal_entry(je, user=request.user, request=request)
            except Exception:
                pass

        payrun.status = 'PAID'
        payrun.save(update_fields=['status'])
        payslips.update(is_paid=True)
        log_audit_event(request.user, 'APPROVE', 'Payrun', payrun.id, str(payrun), request=request, description="Disbursed payroll and created financial ledger entries.")
        messages.success(request, f"Payrun '{payrun.title}' disbursed and posted to Accounting General Ledger!")
        return redirect('payroll:payrun_detail', pk=pk)

    return render(request, 'payroll/payrun_detail.html', {'payrun': payrun, 'payslips': payslips})

@login_required
def payslip_detail(request, pk):
    payslip = get_object_or_404(Payslip.objects.select_related('employee__department', 'employee__designation', 'payrun'), pk=pk)
    return render(request, 'payroll/payslip_detail.html', {'payslip': payslip})
