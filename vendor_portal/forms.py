from django import forms
from decimal import Decimal
from .models import (
    VendorPortalProfile, SupplierBidRfq, SupplierBidSubmission,
    AdvanceShippingNotice, VendorInvoiceUpload, ThreeWayMatchVerification
)
from purchasing.models import Supplier, PurchaseOrder
from inventory.models import Product

class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = VendorPortalProfile
        fields = ['supplier', 'vendor_code', 'rating_score', 'compliance_status', 'bank_swift_code', 'bank_iban', 'tax_id_number', 'is_approved']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'vendor_code': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'rating_score': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'step': '0.1'}),
            'compliance_status': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'bank_swift_code': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'bank_iban': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'tax_id_number': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 dark:border-slate-600 text-indigo-600'}),
        }


class BidSubmissionForm(forms.ModelForm):
    class Meta:
        model = SupplierBidSubmission
        fields = ['rfq', 'vendor', 'total_bid_amount', 'lead_time_days', 'warranty_months', 'vendor_remarks']
        widgets = {
            'rfq': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'vendor': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'total_bid_amount': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'step': '0.01'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'warranty_months': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'vendor_remarks': forms.Textarea(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'rows': 3}),
        }


class ASNCreateForm(forms.ModelForm):
    class Meta:
        model = AdvanceShippingNotice
        fields = ['vendor', 'purchase_order', 'asn_number', 'carrier_name', 'tracking_number', 'dispatch_date', 'estimated_arrival_date', 'package_count', 'notes']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'purchase_order': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'asn_number': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'carrier_name': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'tracking_number': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'dispatch_date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'type': 'date'}),
            'estimated_arrival_date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'type': 'date'}),
            'package_count': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'notes': forms.Textarea(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'rows': 2}),
        }


class VendorInvoiceForm(forms.ModelForm):
    class Meta:
        model = VendorInvoiceUpload
        fields = ['vendor', 'purchase_order', 'invoice_number', 'invoice_date', 'subtotal_amount', 'tax_amount', 'total_amount', 'pdf_document_url']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'purchase_order': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'invoice_number': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'invoice_date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'type': 'date'}),
            'subtotal_amount': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'step': '0.01'}),
            'pdf_document_url': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'placeholder': 'https://docs.nexora.internal/invoices/inv-001.pdf'}),
        }
