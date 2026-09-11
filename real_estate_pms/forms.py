from django import forms
from .models import (
    PropertyComplex, PropertyUnit, PropertyTenant, LeaseAgreement,
    TenantRentInvoice, MaintenanceWorkOrder
)

class PropertyComplexForm(forms.ModelForm):
    class Meta:
        model = PropertyComplex
        fields = ['name', 'code', 'property_type', 'address', 'city', 'state', 'postal_code', 'total_floors', 'total_units_count', 'manager_name', 'manager_phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'total_floors': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_units_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'manager_name': forms.TextInput(attrs={'class': 'form-control'}),
            'manager_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PropertyUnitForm(forms.ModelForm):
    class Meta:
        model = PropertyUnit
        fields = ['complex', 'unit_number', 'floor_number', 'unit_type', 'square_feet', 'base_monthly_rent', 'cam_fee_monthly', 'security_deposit', 'occupancy_status', 'amenities']
        widgets = {
            'complex': forms.Select(attrs={'class': 'form-select'}),
            'unit_number': forms.TextInput(attrs={'class': 'form-control'}),
            'floor_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_type': forms.Select(attrs={'class': 'form-select'}),
            'square_feet': forms.NumberInput(attrs={'class': 'form-control'}),
            'base_monthly_rent': forms.NumberInput(attrs={'class': 'form-control'}),
            'cam_fee_monthly': forms.NumberInput(attrs={'class': 'form-control'}),
            'security_deposit': forms.NumberInput(attrs={'class': 'form-control'}),
            'occupancy_status': forms.Select(attrs={'class': 'form-select'}),
            'amenities': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class LeaseAgreementForm(forms.ModelForm):
    class Meta:
        model = LeaseAgreement
        fields = ['unit', 'tenant', 'start_date', 'end_date', 'monthly_rent', 'cam_fee_monthly', 'security_deposit_held', 'annual_escalation_pct', 'payment_due_day', 'terms_and_conditions']
        widgets = {
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'form-control'}),
            'cam_fee_monthly': forms.NumberInput(attrs={'class': 'form-control'}),
            'security_deposit_held': forms.NumberInput(attrs={'class': 'form-control'}),
            'annual_escalation_pct': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_due_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 28}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MaintenanceWorkOrderForm(forms.ModelForm):
    class Meta:
        model = MaintenanceWorkOrder
        fields = ['unit', 'tenant', 'issue_title', 'description', 'category', 'priority', 'estimated_cost', 'assigned_technician']
        widgets = {
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'issue_title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'assigned_technician': forms.TextInput(attrs={'class': 'form-control'}),
        }
