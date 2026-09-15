from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from hr.models import Employee

class TaxJurisdictionRule(models.Model):
    country_code = models.CharField(max_length=10, unique=True) # US, GB, DE, IN, SG
    country_name = models.CharField(max_length=100)
    statutory_tax_name = models.CharField(max_length=150, help_text="e.g. US Federal Income Tax & FICA")
    income_tax_effective_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'))
    social_security_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('6.20'))
    healthcare_insurance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.45'))
    pension_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    employer_contribution_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('8.50'))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['country_code']
        verbose_name = 'Tax Jurisdiction Statutory Rule'
        verbose_name_plural = 'Tax Jurisdiction Statutory Rules'

    def __str__(self):
        return f"{self.country_code} - {self.country_name} ({self.statutory_tax_name})"


class SalaryStructure(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='localized_salary_structure')
    jurisdiction = models.ForeignKey(TaxJurisdictionRule, on_delete=models.PROTECT, related_name='salaries')
    currency = models.CharField(max_length=10, default='USD')
    base_monthly_salary = models.DecimalField(max_digits=12, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['employee']
        verbose_name = 'Employee Salary Structure'
        verbose_name_plural = 'Employee Salary Structures'

    def __str__(self):
        return f"{self.employee}: {self.currency} ${self.total_gross_salary:,.2f} Gross/mo"

    @property
    def total_allowances(self):
        return self.housing_allowance + self.transport_allowance + self.special_allowance

    @property
    def total_gross_salary(self):
        return self.base_monthly_salary + self.total_allowances


class PayRunBatch(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft Batch Run'),
        ('CALCULATED', 'Gross-to-Net Calculated'),
        ('APPROVED', 'Approved by CFO / Payroll Director'),
        ('POSTED_GL', 'Posted to General Ledger'),
    ]

    batch_number = models.CharField(max_length=50, unique=True)
    period_month = models.PositiveSmallIntegerField() # 1-12
    period_year = models.PositiveSmallIntegerField() # 2026
    pay_date = models.DateField()
    
    total_gross_disbursed = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_statutory_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_net_disbursed = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_payslips_count = models.PositiveIntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_year', '-period_month']
        verbose_name = 'Pay Run Batch'
        verbose_name_plural = 'Pay Run Batches'

    def __str__(self):
        return f"Pay Run #{self.batch_number} ({self.period_year}-{self.period_month:02d}) - Net: ${self.total_net_disbursed:,.2f}"


class EmployeePayslip(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft Calculated'),
        ('FINALIZED', 'Finalized & Locked'),
        ('PAID', 'Disbursed & Paid'),
    ]

    pay_run = models.ForeignKey(PayRunBatch, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='localized_payslips')
    currency = models.CharField(max_length=10, default='USD')

    base_earnings = models.DecimalField(max_digits=12, decimal_places=2)
    total_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)

    statutory_income_tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    social_insurance_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pension_employee_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)

    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    employer_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('pay_run', 'employee')
        ordering = ['-pay_run', 'employee']
        verbose_name = 'Employee Itemized Payslip'
        verbose_name_plural = 'Employee Itemized Payslips'

    def __str__(self):
        return f"Payslip {self.pay_run.batch_number} - {self.employee}: Net {self.currency} ${self.net_pay:,.2f}"
