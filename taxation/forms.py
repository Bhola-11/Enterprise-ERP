from django import forms
from .models import (
    TaxJurisdiction, HSNSACCode, GSTTaxRate, EWayBillRecord,
    EInvoiceIRN, EUVATRule, USStateNexusRate, TaxFilingReturn
)


class TaxJurisdictionForm(forms.ModelForm):
    class Meta:
        model = TaxJurisdiction
        fields = [
            'country', 'name', 'code', 'tax_authority_name', 'filing_frequency',
            'currency', 'is_default', 'e_invoicing_mandatory', 'e_way_bill_mandatory',
            'e_way_bill_threshold'
        ]
        widgets = {
            'country': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'tax_authority_name': forms.TextInput(attrs={'class': 'form-control'}),
            'filing_frequency': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'e_invoicing_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'e_way_bill_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'e_way_bill_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class HSNSACCodeForm(forms.ModelForm):
    class Meta:
        model = HSNSACCode
        fields = ['code', 'description', 'code_type', 'standard_gst_rate', 'is_exempt', 'is_nil_rated', 'rcm_applicable']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control font-monospace'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'code_type': forms.Select(attrs={'class': 'form-select'}),
            'standard_gst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_nil_rated': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rcm_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EWayBillGenerateForm(forms.ModelForm):
    class Meta:
        model = EWayBillRecord
        fields = [
            'document_number', 'document_type', 'transport_mode', 'vehicle_number',
            'transporter_id', 'transporter_name', 'distance_km', 'from_pincode',
            'to_pincode', 'total_invoice_value'
        ]
        widgets = {
            'document_number': forms.TextInput(attrs={'class': 'form-control font-monospace'}),
            'document_type': forms.TextInput(attrs={'class': 'form-control'}),
            'transport_mode': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control font-monospace text-uppercase'}),
            'transporter_id': forms.TextInput(attrs={'class': 'form-control font-monospace text-uppercase'}),
            'transporter_name': forms.TextInput(attrs={'class': 'form-control'}),
            'distance_km': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'from_pincode': forms.TextInput(attrs={'class': 'form-control font-monospace'}),
            'to_pincode': forms.TextInput(attrs={'class': 'form-control font-monospace'}),
            'total_invoice_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class TaxFilingReturnForm(forms.ModelForm):
    class Meta:
        model = TaxFilingReturn
        fields = [
            'jurisdiction', 'return_type', 'period_start', 'period_end',
            'total_taxable_turnover', 'total_tax_collected', 'total_itc_claimed',
            'net_tax_payable', 'status', 'government_arn_reference'
        ]
        widgets = {
            'jurisdiction': forms.Select(attrs={'class': 'form-select'}),
            'return_type': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_taxable_turnover': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_tax_collected': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_itc_claimed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'net_tax_payable': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'government_arn_reference': forms.TextInput(attrs={'class': 'form-control font-monospace'}),
        }
