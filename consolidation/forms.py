from django import forms
from .models import ConsolidationGroup, CurrencyExchangeRate, InterCompanyEliminationRule, ConsolidatedStatement

class ConsolidationGroupForm(forms.ModelForm):
    class Meta:
        model = ConsolidationGroup
        fields = ['name', 'code', 'parent_organization', 'subsidiary_organizations', 'reporting_currency', 'fiscal_year_end_month', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_organization': forms.Select(attrs={'class': 'form-select'}),
            'subsidiary_organizations': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
            'reporting_currency': forms.TextInput(attrs={'class': 'form-control'}),
            'fiscal_year_end_month': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CurrencyExchangeRateForm(forms.ModelForm):
    class Meta:
        model = CurrencyExchangeRate
        fields = ['from_currency', 'to_currency', 'effective_date', 'spot_rate', 'average_monthly_rate', 'closing_rate']
        widgets = {
            'from_currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EUR'}),
            'to_currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'USD'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'spot_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'average_monthly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'closing_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
        }


class InterCompanyEliminationRuleForm(forms.ModelForm):
    class Meta:
        model = InterCompanyEliminationRule
        fields = ['group', 'rule_name', 'rule_type', 'source_account_code', 'offset_account_code', 'is_active']
        widgets = {
            'group': forms.Select(attrs={'class': 'form-select'}),
            'rule_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'source_account_code': forms.TextInput(attrs={'class': 'form-control'}),
            'offset_account_code': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RunConsolidationForm(forms.Form):
    group = forms.ModelChoiceField(queryset=ConsolidationGroup.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-select'}))
    statement_type = forms.ChoiceField(choices=ConsolidatedStatement.STATEMENT_TYPES, widget=forms.Select(attrs={'class': 'form-select'}))
    period_start = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    period_end = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))