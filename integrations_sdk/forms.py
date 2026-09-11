from django import forms
from .models import IntegrationConnector

class IntegrationConnectorForm(forms.ModelForm):
    api_key_or_token = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control font-monospace', 'placeholder': 'sk_live_... or Bearer Token'}),
        help_text="Encrypted API token or secret"
    )

    class Meta:
        model = IntegrationConnector
        fields = ['name', 'connector_type', 'auth_type', 'base_url', 'sync_interval_minutes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'connector_type': forms.Select(attrs={'class': 'form-select'}),
            'auth_type': forms.Select(attrs={'class': 'form-select'}),
            'base_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://api.stripe.com/v1'}),
            'sync_interval_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        token = self.cleaned_data.get('api_key_or_token')
        if token:
            masked = f"{token[:6]}...{token[-4:]}" if len(token) > 10 else "***"
            instance.credentials_config = {'token_masked': masked}
        if commit:
            instance.save()
        return instance