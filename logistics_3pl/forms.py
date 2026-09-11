from django import forms
from .models import (
    ShippingCarrier, FreightRateMatrix, FreightConsignment,
    FreightConsignmentItem, TransitMilestoneCheckpoint
)


class ShippingCarrierForm(forms.ModelForm):
    class Meta:
        model = ShippingCarrier
        fields = ['name', 'code', 'carrier_type', 'contact_person', 'contact_phone', 'contact_email', 'tracking_url_template', 'account_number', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control text-uppercase font-monospace'}),
            'carrier_type': forms.Select(attrs={'class': 'form-select'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tracking_url_template': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control font-monospace'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FreightConsignmentBookingForm(forms.ModelForm):
    class Meta:
        model = FreightConsignment
        fields = [
            'carrier', 'customer', 'transport_mode', 'incoterms',
            'shipper_name', 'shipper_address', 'shipper_city', 'shipper_country',
            'consignee_name', 'consignee_address', 'consignee_city', 'consignee_country',
            'origin_hub', 'destination_hub', 'total_packages_count',
            'actual_gross_weight_kg', 'volumetric_weight_kg', 'chargeable_weight_kg',
            'total_volume_cbm', 'declared_customs_value', 'notes'
        ]
        widgets = {
            'carrier': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'transport_mode': forms.Select(attrs={'class': 'form-select'}),
            'incoterms': forms.Select(attrs={'class': 'form-select'}),
            'shipper_name': forms.TextInput(attrs={'class': 'form-control'}),
            'shipper_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'shipper_city': forms.TextInput(attrs={'class': 'form-control'}),
            'shipper_country': forms.TextInput(attrs={'class': 'form-control'}),
            'consignee_name': forms.TextInput(attrs={'class': 'form-control'}),
            'consignee_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'consignee_city': forms.TextInput(attrs={'class': 'form-control'}),
            'consignee_country': forms.TextInput(attrs={'class': 'form-control'}),
            'origin_hub': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_hub': forms.TextInput(attrs={'class': 'form-control'}),
            'total_packages_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'actual_gross_weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volumetric_weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'chargeable_weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_volume_cbm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'declared_customs_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class TransitMilestoneForm(forms.ModelForm):
    class Meta:
        model = TransitMilestoneCheckpoint
        fields = ['location_city', 'facility_name', 'status_title', 'description', 'latitude', 'longitude']
        widgets = {
            'location_city': forms.TextInput(attrs={'class': 'form-control'}),
            'facility_name': forms.TextInput(attrs={'class': 'form-control'}),
            'status_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Arrived at Sort Facility, Customs Cleared, Out for Delivery'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
        }
