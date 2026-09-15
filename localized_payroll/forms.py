from django import forms
from .models import TaxJurisdictionRule, SalaryStructure, PayRunBatch

class TaxJurisdictionRuleForm(forms.ModelForm):
    class Meta:
        model = TaxJurisdictionRule
        fields = [
            'country_code', 'country_name', 'statutory_tax_name',
            'income_tax_effective_rate', 'social_security_rate',
            'healthcare_insurance_rate', 'pension_employee_rate',
            'employer_contribution_rate', 'is_active'
        ]
        widgets = {
            'country_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country_name': forms.TextInput(attrs={'class': 'form-control'}),
            'statutory_tax_name': forms.TextInput(attrs={'class': 'form-control'}),
            'income_tax_effective_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'social_security_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'healthcare_insurance_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pension_employee_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'employer_contribution_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SalaryStructureForm(forms.ModelForm):
    class Meta:
        model = SalaryStructure
        fields = [
            'employee', 'jurisdiction', 'currency',
            'base_monthly_salary', 'housing_allowance',
            'transport_allowance', 'special_allowance', 'is_active'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'jurisdiction': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'base_monthly_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'housing_allowance': forms.NumberInput(attrs={'class': 'form-control'}),
            'transport_allowance': forms.NumberInput(attrs={'class': 'form-control'}),
            'special_allowance': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PayRunLaunchForm(forms.Form):
    period_month = forms.IntegerField(min_value=1, max_value=12, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    period_year = forms.IntegerField(min_value=2020, max_value=2035, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    pay_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
