from django import forms
from .models import (
    POSTerminal, POSSession, POSCashTransaction, POSCouponPromotion,
    POSCustomerLoyalty
)


class POSTerminalForm(forms.ModelForm):
    class Meta:
        model = POSTerminal
        fields = [
            'terminal_code', 'name', 'branch', 'warehouse', 'cash_account',
            'ip_address', 'receipt_header', 'receipt_footer', 'allow_offline_orders', 'status'
        ]
        widgets = {
            'terminal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'POS-TRM-01'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Main Checkout 1'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'cash_account': forms.Select(attrs={'class': 'form-select'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.1.100'}),
            'receipt_header': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'receipt_footer': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'allow_offline_orders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class POSSessionOpenForm(forms.ModelForm):
    class Meta:
        model = POSSession
        fields = ['opening_cash', 'opening_notes']
        widgets = {
            'opening_cash': forms.NumberInput(attrs={'class': 'form-control form-control-lg text-end font-monospace', 'step': '0.01', 'min': '0'}),
            'opening_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Shift opening notes or drawer denominations...'}),
        }


class POSSessionCloseForm(forms.ModelForm):
    class Meta:
        model = POSSession
        fields = ['counted_cash', 'closing_notes']
        widgets = {
            'counted_cash': forms.NumberInput(attrs={'class': 'form-control form-control-lg text-end font-monospace', 'step': '0.01', 'min': '0'}),
            'closing_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Cash denomination count breakdown, discrepancies notes...'}),
        }


class POSCashTransactionForm(forms.ModelForm):
    class Meta:
        model = POSCashTransaction
        fields = ['transaction_type', 'amount', 'reason']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Midday safe drop, petty cash supplies purchase'}),
        }


class POSCouponForm(forms.ModelForm):
    class Meta:
        model = POSCouponPromotion
        fields = [
            'code', 'name', 'discount_type', 'discount_value', 'min_order_value',
            'max_discount_cap', 'valid_from', 'valid_to', 'usage_limit', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_order_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_discount_cap': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
