from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from hr.models import Employee, Department, Designation
from organizations.models import Organization, Branch
from localized_payroll.models import TaxJurisdictionRule, SalaryStructure, PayRunBatch, EmployeePayslip
from localized_payroll.services import GrossToNetPayrollEngine

User = get_user_model()

class LocalizedPayrollTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='payroll_director',
            email='payroll_dir@nexora.io',
            password='Password123!'
        )
        self.org = Organization.objects.create(name='Nexora USA Inc.', currency='USD')
        self.branch = Branch.objects.create(organization=self.org, name='US HQ', code='HQ-NYC')
        self.dept = Department.objects.create(organization=self.org, name='Corporate Finance', code='FIN', branch=self.branch)
        self.des_cpa = Designation.objects.create(title='Senior Financial Analyst', code='DES-FIN-01', department=self.dept)

        self.emp = Employee.objects.create(
            employee_id='EMP-LP-001', first_name='Alexander', last_name='Wright',
            email='a.wright@nexora.io', department=self.dept, designation=self.des_cpa,
            branch=self.branch, joining_date=date(2023, 1, 1), status='ACTIVE'
        )

        self.jur_us = TaxJurisdictionRule.objects.create(
            country_code='US',
            country_name='United States',
            statutory_tax_name='US Federal W-4 & FICA',
            income_tax_effective_rate=Decimal('20.00'),
            social_security_rate=Decimal('6.20'),
            healthcare_insurance_rate=Decimal('1.45'),
            pension_employee_rate=Decimal('5.00'),
            employer_contribution_rate=Decimal('8.50')
        )

        self.salary = SalaryStructure.objects.create(
            employee=self.emp,
            jurisdiction=self.jur_us,
            currency='USD',
            base_monthly_salary=Decimal('10000.00'),
            housing_allowance=Decimal('1500.00'),
            transport_allowance=Decimal('500.00'),
            special_allowance=Decimal('0.00')
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_gross_to_net_calculation(self):
        # Gross = 10,000 base + 2,000 allowances = 12,000.00
        self.assertEqual(self.salary.total_gross_salary, Decimal('12000.00'))

        batch = GrossToNetPayrollEngine.execute_batch_pay_run(
            period_month=3,
            period_year=2026,
            pay_date=date(2026, 3, 31),
            user=self.user
        )

        self.assertEqual(batch.status, 'APPROVED')
        self.assertEqual(batch.total_payslips_count, 1)
        self.assertEqual(batch.total_gross_disbursed, Decimal('12000.00'))

        payslip = batch.payslips.first()
        # Tax: 20% of 12,000 = 2,400.00
        # Social Sec + Health: 7.65% of 12,000 = 918.00
        # Pension: 5% of 12,000 = 600.00
        # Total Deductions: 3,918.00
        # Net Pay: 8,082.00
        self.assertEqual(payslip.statutory_income_tax, Decimal('2400.00'))
        self.assertEqual(payslip.social_insurance_deduction, Decimal('918.00'))
        self.assertEqual(payslip.pension_employee_deduction, Decimal('600.00'))
        self.assertEqual(payslip.total_deductions, Decimal('3918.00'))
        self.assertEqual(payslip.net_pay, Decimal('8082.00'))

    def test_views(self):
        batch = GrossToNetPayrollEngine.execute_batch_pay_run(
            period_month=3,
            period_year=2026,
            pay_date=date(2026, 3, 31),
            user=self.user
        )
        ps = batch.payslips.first()

        res_dash = self.client.get(reverse('localized_payroll:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_runs = self.client.get(reverse('localized_payroll:payrun_list'))
        self.assertEqual(res_runs.status_code, 200)

        res_batch = self.client.get(reverse('localized_payroll:payrun_detail', args=[batch.id]))
        self.assertEqual(res_batch.status_code, 200)

        res_ps = self.client.get(reverse('localized_payroll:payslip_detail', args=[ps.id]))
        self.assertEqual(res_ps.status_code, 200)

        res_salaries = self.client.get(reverse('localized_payroll:salary_list'))
        self.assertEqual(res_salaries.status_code, 200)

        res_jur = self.client.get(reverse('localized_payroll:jurisdictions_list'))
        self.assertEqual(res_jur.status_code, 200)
