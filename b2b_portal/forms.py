from django import forms
from decimal import Decimal
from .models import B2BAccount, B2BCatalogPriceTier, QuoteApprovalRequest, SelfServiceOrder, DigitalPaymentTransaction
from sales.models import Customer
from crm.models import Contact
from inventory.models import Product

class B2BAccountForm(forms.ModelForm):
    class Meta:
        model = B2BAccount
        fields = [
            'customer', 'account_number', 'primary_contact',
            'credit_limit', 'payment_terms', 'discount_tier_name',
            'tax_exemption_number', 'portal_access_enabled', 'is_active'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'account_number': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'primary_contact': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'step': '1000'}),
            'payment_terms': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'discount_tier_name': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'tax_exemption_number': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'portal_access_enabled': forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 dark:border-slate-600 text-indigo-600'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 dark:border-slate-600 text-indigo-600'}),
        }


class PriceTierForm(forms.ModelForm):
    class Meta:
        model = B2BCatalogPriceTier
        fields = ['b2b_account', 'product', 'min_quantity', 'tier_unit_price', 'discount_percentage', 'effective_from', 'effective_to', 'is_active']
        widgets = {
            'b2b_account': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'product': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'tier_unit_price': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'step': '0.1'}),
            'effective_from': forms.DateInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 dark:border-slate-600 text-indigo-600'}),
        }


class QuoteActionForm(forms.Form):
    action = forms.ChoiceField(
        choices=[('APPROVE', 'Approve Quotation'), ('REJECT', 'Reject Quotation')],
        widget=forms.RadioSelect(attrs={'class': 'text-indigo-600 focus:ring-indigo-500'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'rows': 3, 'placeholder': 'Optional customer decision comments or PO reference...'})
    )


class QuickOrderForm(forms.Form):
    po_reference = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'placeholder': 'e.g. PO-2026-US-884'})
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        widget=forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'})
    )
    quantity = forms.IntegerField(
        min_value=1, initial=10,
        widget=forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'})
    )
    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'rows': 2, 'placeholder': 'Delivery dock / facility address'})
    )
    requested_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'type': 'date'})
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['product'].queryset = Product.objects.filter(organization=organization, is_active=True)
        else:
            self.fields['product'].queryset = Product.objects.all()


class PaymentCheckoutForm(forms.Form):
    gateway = forms.ChoiceField(
        choices=DigitalPaymentTransaction.GATEWAY_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'})
    )
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'step': '0.01'})
    )
    payment_token = forms.CharField(
        max_length=100, initial='tok_enterprise_ach_authorized_2026',
        widget=forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm font-mono'})
    )
