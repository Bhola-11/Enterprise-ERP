import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import TaxJurisdictionRule, SalaryStructure, PayRunBatch, EmployeePayslip
from accounting.models import JournalEntry, JournalItem, Account

class GrossToNetPayrollEngine:
    @classmethod
    @transaction.atomic
    def execute_batch_pay_run(cls, period_month, period_year, pay_date, user=None):
        batch_no = f"PR-{period_year}{period_month:02d}-{uuid.uuid4().hex[:4].upper()}"

        batch = PayRunBatch.objects.create(
            batch_number=batch_no,
            period_month=period_month,
            period_year=period_year,
            pay_date=pay_date,
            status='DRAFT',
            created_by=user
        )

        salaries = SalaryStructure.objects.filter(is_active=True).select_related('employee', 'jurisdiction')
        payslips = []

        total_gross = Decimal('0.00')
        total_ded = Decimal('0.00')
        total_net = Decimal('0.00')

        for sal in salaries:
            emp = sal.employee
            jur = sal.jurisdiction

            base = sal.base_monthly_salary
            allowances = sal.total_allowances
            gross = base + allowances

            # Statutory Calculations
            tax_rate = jur.income_tax_effective_rate / Decimal('100.0')
            social_rate = (jur.social_security_rate + jur.healthcare_insurance_rate) / Decimal('100.0')
            pension_rate = jur.pension_employee_rate / Decimal('100.0')
            er_contrib_rate = jur.employer_contribution_rate / Decimal('100.0')

            income_tax = (gross * tax_rate).quantize(Decimal('0.01'))
            social_sec = (gross * social_rate).quantize(Decimal('0.01'))
            pension = (gross * pension_rate).quantize(Decimal('0.01'))
            deductions = income_tax + social_sec + pension

            net = gross - deductions
            er_contrib = (gross * er_contrib_rate).quantize(Decimal('0.01'))

            total_gross += gross
            total_ded += deductions
            total_net += net

            ps = EmployeePayslip(
                pay_run=batch,
                employee=emp,
                currency=sal.currency,
                base_earnings=base,
                total_allowances=allowances,
                gross_pay=gross,
                statutory_income_tax=income_tax,
                social_insurance_deduction=social_sec,
                pension_employee_deduction=pension,
                total_deductions=deductions,
                net_pay=net,
                employer_contribution=er_contrib,
                status='FINALIZED'
            )
            payslips.append(ps)

        EmployeePayslip.objects.bulk_create(payslips)

        batch.total_gross_disbursed = total_gross
        batch.total_statutory_deductions = total_ded
        batch.total_net_disbursed = total_net
        batch.total_payslips_count = len(payslips)
        batch.status = 'APPROVED'
        batch.save(update_fields=['total_gross_disbursed', 'total_statutory_deductions', 'total_net_disbursed', 'total_payslips_count', 'status'])

        return batch
