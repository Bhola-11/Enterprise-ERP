from django import forms
from .models import DepreciableAsset, AssetImpairmentRecord, AssetDisposalRecord

class DepreciableAssetForm(forms.ModelForm):
    class Meta:
        model = DepreciableAsset
        fields = [
            'asset_tag', 'asset_name', 'category_name', 'acquisition_date',
            'acquisition_cost', 'salvage_value', 'useful_life_months',
            'depreciation_method', 'asset_gl_account', 'accumulated_depr_gl_account',
            'depreciation_expense_gl_account', 'location_facility', 'notes'
        ]
        widgets = {
            'asset_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category_name': forms.TextInput(attrs={'class': 'form-control'}),
            'acquisition_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'acquisition_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'salvage_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'useful_life_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'depreciation_method': forms.Select(attrs={'class': 'form-select'}),
            'asset_gl_account': forms.Select(attrs={'class': 'form-select'}),
            'accumulated_depr_gl_account': forms.Select(attrs={'class': 'form-select'}),
            'depreciation_expense_gl_account': forms.Select(attrs={'class': 'form-select'}),
            'location_facility': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AssetImpairmentForm(forms.Form):
    recoverable_amount = forms.DecimalField(max_digits=15, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    reason = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))


class AssetDisposalForm(forms.Form):
    sale_proceeds = forms.DecimalField(max_digits=15, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    buyer_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))