from django.contrib import admin
from .models import Organization, Branch, Department, CostCenter, FiscalYear, TaxSetting

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'tax_id', 'currency', 'email', 'phone', 'city', 'country')

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager', 'city', 'is_headquarters', 'is_active')
    list_filter = ('is_headquarters', 'is_active')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager_name', 'budget', 'branch', 'is_active')
    list_filter = ('branch', 'is_active')

@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'budget_allocated', 'budget_spent', 'is_active')

@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'is_closed', 'is_active')

@admin.register(TaxSetting)
class TaxSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'tax_code', 'is_compound', 'is_active')
