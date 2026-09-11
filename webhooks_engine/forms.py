from django import forms
from .models import WebhookEndpoint
from .services import WebhookDispatcher, HMACSignatureEngine

class WebhookEndpointForm(forms.ModelForm):
    subscribed_topics = forms.MultipleChoiceField(
        choices=WebhookDispatcher.AVAILABLE_TOPICS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )

    class Meta:
        model = WebhookEndpoint
        fields = ['name', 'target_url', 'secret_key', 'retry_limit', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'target_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://api.externalpartner.com/webhooks/nexora'}),
            'secret_key': forms.TextInput(attrs={'class': 'form-control font-monospace'}),
            'retry_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('secret_key'):
            self.initial['secret_key'] = HMACSignatureEngine.generate_secret()
        if self.instance and self.instance.pk:
            self.initial['subscribed_topics'] = self.instance.subscribed_events

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.subscribed_events = self.cleaned_data['subscribed_topics']
        if commit:
            instance.save()
        return instance


class TestWebhookTriggerForm(forms.Form):
    topic = forms.ChoiceField(choices=WebhookDispatcher.AVAILABLE_TOPICS, widget=forms.Select(attrs={'class': 'form-select'}))
    sample_payload = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 5}),
        initial='{\n  "order_number": "SO-2026-9001",\n  "total_amount": "4500.00",\n  "customer": "Global Aerospace LLC"\n}'
    )