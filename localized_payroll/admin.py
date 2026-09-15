from django.contrib import admin
from .models import TaxJurisdictionRule, SalaryStructure, PayRunBatch, EmployeePayslip

class EmployeePayslipInline(admin.TabularInline):
    model = EmployeePayslip
    extra = 0
    readonly_fields = ('employee', 'currency', 'gross_pay', 'total_deductions', 'net_pay', 'status')

@admin.register(TaxJurisdictionRule)
class TaxJurisdictionRuleAdmin(admin.ModelAdmin):
    list_display = ('country_code', 'country_name', 'statutory_tax_name', 'income_tax_effective_rate', 'is_active')
    list_filter = ('is_active', 'country_code')

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ('employee', 'jurisdiction', 'currency', 'base_monthly_salary', 'total_gross_salary', 'is_active')
    list_filter = ('jurisdiction', 'currency', 'is_active')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(PayRunBatch)
class PayRunBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'period_year', 'period_month', 'total_gross_disbursed', 'total_net_disbursed', 'total_payslips_count', 'status')
    list_filter = ('period_year', 'period_month', 'status')
    inlines = [EmployeePayslipInline]

@admin.register(EmployeePayslip)
class EmployeePayslipAdmin(admin.ModelAdmin):
    list_display = ('pay_run', 'employee', 'gross_pay', 'total_deductions', 'net_pay', 'status')
    list_filter = ('status', 'pay_run__period_year')
    search_fields = ('employee__first_name', 'employee__last_name')
