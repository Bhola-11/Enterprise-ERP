from django.contrib import admin
from .models import SalaryStructure, Payrun, Payslip

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ('employee', 'basic_salary', 'gross_salary', 'net_salary')

class PayslipInline(admin.TabularInline):
    model = Payslip
    extra = 0
    readonly_fields = ('employee', 'basic_salary', 'allowances', 'gross_salary', 'deductions', 'net_salary', 'is_paid')

@admin.register(Payrun)
class PayrunAdmin(admin.ModelAdmin):
    list_display = ('title', 'month', 'year', 'total_gross', 'total_net', 'status', 'created_at')
    list_filter = ('status', 'year')
    inlines = [PayslipInline]

@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'payrun', 'gross_salary', 'net_salary', 'payment_method', 'is_paid')
    list_filter = ('is_paid', 'payrun')
