from django import forms
from .models import CashPoolHeader, CashPoolParticipant, LiquidityForecast, FXHedgingContract

class CashPoolHeaderForm(forms.ModelForm):
    class Meta:
        model = CashPoolHeader
        fields = ['name', 'pool_code', 'pool_method', 'pool_leader_bank', 'target_balance_amount', 'currency', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'pool_code': forms.TextInput(attrs={'class': 'form-control'}),
            'pool_method': forms.Select(attrs={'class': 'form-select'}),
            'pool_leader_bank': forms.Select(attrs={'class': 'form-select'}),
            'target_balance_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CashPoolParticipantForm(forms.ModelForm):
    class Meta:
        model = CashPoolParticipant
        fields = ['bank_account', 'priority', 'min_transfer_threshold', 'is_active']
        widgets = {
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_transfer_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FXHedgingContractForm(forms.ModelForm):
    class Meta:
        model = FXHedgingContract
        fields = ['contract_number', 'contract_type', 'counterparty_bank', 'notional_amount', 'base_currency', 'quote_currency', 'strike_rate', 'maturity_date', 'mark_to_market_value', 'status']
        widgets = {
            'contract_number': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'counterparty_bank': forms.TextInput(attrs={'class': 'form-control'}),
            'notional_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'base_currency': forms.TextInput(attrs={'class': 'form-control'}),
            'quote_currency': forms.TextInput(attrs={'class': 'form-control'}),
            'strike_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'maturity_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'mark_to_market_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }