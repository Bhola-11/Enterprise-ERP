from django import forms
from .models import APIClient, APIKey, RateLimitPolicy

class RateLimitPolicyForm(forms.ModelForm):
    class Meta:
        model = RateLimitPolicy
        fields = ['name', 'requests_per_minute', 'requests_per_hour', 'burst_limit', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'requests_per_minute': forms.NumberInput(attrs={'class': 'form-control'}),
            'requests_per_hour': forms.NumberInput(attrs={'class': 'form-control'}),
            'burst_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class APIClientForm(forms.ModelForm):
    class Meta:
        model = APIClient
        fields = ['client_name', 'organization', 'contact_email', 'rate_limit_policy', 'ip_whitelist', 'allowed_scopes', 'is_active']
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rate_limit_policy': forms.Select(attrs={'class': 'form-select'}),
            'ip_whitelist': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. 192.168.1.1, 10.0.0.0/24'}),
            'allowed_scopes': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class APIKeyGenerationForm(forms.Form):
    name = forms.CharField(max_length=150, initial="Production Microservice Key", widget=forms.TextInput(attrs={'class': 'form-control'}))
    key_type = forms.ChoiceField(choices=APIKey.KEY_TYPES, widget=forms.Select(attrs={'class': 'form-select'}))
    expires_in_days = forms.IntegerField(initial=365, widget=forms.NumberInput(attrs={'class': 'form-control'}))