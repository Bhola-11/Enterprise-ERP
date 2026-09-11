from django import forms
from .models import Asset, AssetCategory, AssetMaintenanceLog

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_tag', 'name', 'category', 'serial_number', 'purchase_date', 'purchase_cost', 'current_value', 'salvage_value', 'status', 'assigned_to', 'location', 'warranty_expiry', 'notes']
        widgets = {
            'asset_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'salvage_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
