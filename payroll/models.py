from django.db import models
from django.conf import settings
from decimal import Decimal
from hr.models import Employee

class SalaryStructure(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=5000.00)
    hra_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=1500.00)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=500.00)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=300.00)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=200.00)
    provident_fund = models.DecimalField(max_digits=12, decimal_places=2, default=400.00)
    tax_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=600.00)

    @property
    def total_allowances(self):
        return self.hra_allowance + self.transport_allowance + self.medical_allowance + self.special_allowance

    @property
    def gross_salary(self):
        return self.basic_salary + self.total_allowances

    @property
    def total_deductions(self):
        return self.provident_fund + self.tax_deduction

    @property
    def net_salary(self):
        return self.gross_salary - self.total_deductions

    def __str__(self):
        return f"{self.employee.full_name} - Gross: ${self.gross_salary:,.2f} | Net: ${self.net_salary:,.2f}"

class Payrun(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Disbursed / Paid'),
    ]

    title = models.CharField(max_length=100) # e.g. "Payroll September 2026"
    month = models.PositiveSmallIntegerField() # 1 - 12
    year = models.PositiveIntegerField() # 2026
    start_date = models.DateField()
    end_date = models.DateField()
    total_gross = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_net = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.title} (${self.total_net:,.2f}) [{self.status}]"

class Payslip(models.Model):
    payrun = models.ForeignKey(Payrun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='payslips')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    deductions = models.DecimalField(max_digits=12, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Direct Deposit')
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('payrun', 'employee')
        ordering = ['employee__employee_id']

    def __str__(self):
        return f"Payslip #{self.id}: {self.employee.full_name} (${self.net_salary:,.2f})"
