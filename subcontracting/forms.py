from django import forms
from .models import SubcontractorVendor, SubcontractOrder, SubcontractGoodsReceipt

class SubcontractorVendorForm(forms.ModelForm):
    class Meta:
        model = SubcontractorVendor
        fields = ['name', 'code', 'vendor_tax_id', 'contact_person', 'contact_email', 'contact_phone', 'facility_address', 'toll_processing_types', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'vendor_tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'facility_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'toll_processing_types': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SubcontractOrderForm(forms.ModelForm):
    class Meta:
        model = SubcontractOrder
        fields = ['subcontractor', 'finished_product', 'planned_quantity', 'unit_processing_rate', 'order_date', 'expected_delivery_date', 'notes']
        widgets = {
            'subcontractor': forms.Select(attrs={'class': 'form-select'}),
            'finished_product': forms.Select(attrs={'class': 'form-select'}),
            'planned_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_processing_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SubcontractGoodsReceiptForm(forms.Form):
    quantity_received = forms.DecimalField(max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    quantity_rejected = forms.DecimalField(max_digits=12, decimal_places=2, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    scrap_material_reported = forms.DecimalField(max_digits=12, decimal_places=2, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    vendor_delivery_note_ref = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor Challan #'}))
