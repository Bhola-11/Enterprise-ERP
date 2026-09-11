from django import forms
from .models import BankStatement, ReconciliationRule, ReconciliationSession


class BankStatementUploadForm(forms.Form):
    bank_account = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    statement_format = forms.ChoiceField(
        choices=BankStatement.STATEMENT_FORMATS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    statement_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.ofx,.qif,.txt'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounting.models import BankAccount
        self.fields['bank_account'].queryset = BankAccount.objects.all()


class ReconciliationRuleForm(forms.ModelForm):
    class Meta:
        model = ReconciliationRule
        fields = [
            'name', 'priority', 'rule_type', 'regex_pattern', 'date_tolerance_days',
            'min_confidence_score', 'auto_post_adjusting_entry', 'contra_account', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'regex_pattern': forms.TextInput(attrs={'class': 'form-control font-monospace'}),
            'date_tolerance_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_confidence_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'auto_post_adjusting_entry': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contra_account': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
