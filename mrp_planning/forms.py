from django import forms
from .models import MasterProductionSchedule, SafetyStockRule, MRPRun

class MasterProductionScheduleForm(forms.ModelForm):
    class Meta:
        model = MasterProductionSchedule
        fields = ['product', 'period_start', 'period_end', 'forecast_demand_qty', 'confirmed_so_qty', 'planned_production_qty', 'status', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'forecast_demand_qty': forms.NumberInput(attrs={'class': 'form-control'}),
            'confirmed_so_qty': forms.NumberInput(attrs={'class': 'form-control'}),
            'planned_production_qty': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SafetyStockRuleForm(forms.ModelForm):
    class Meta:
        model = SafetyStockRule
        fields = ['product', 'warehouse', 'min_safety_stock', 'reorder_point', 'economic_order_quantity', 'lead_time_days', 'is_active']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'min_safety_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_point': forms.NumberInput(attrs={'class': 'form-control'}),
            'economic_order_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MRPExecutionForm(forms.Form):
    planning_horizon_days = forms.IntegerField(initial=90, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    include_forecast = forms.BooleanField(initial=True, required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    include_safety_stock = forms.BooleanField(initial=True, required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
