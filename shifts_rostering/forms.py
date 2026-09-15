from django import forms
from .models import ShiftTemplate, ShiftRosterAssignment, BiometricPunchLog

class ShiftTemplateForm(forms.ModelForm):
    class Meta:
        model = ShiftTemplate
        fields = [
            'name', 'shift_code', 'start_time', 'end_time',
            'break_duration_minutes', 'grace_period_minutes',
            'is_night_shift', 'hourly_rate_multiplier', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'shift_code': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'break_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'grace_period_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_night_shift': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hourly_rate_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ShiftRosterAssignmentForm(forms.ModelForm):
    class Meta:
        model = ShiftRosterAssignment
        fields = ['employee', 'shift_template', 'date', 'status', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'shift_template': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BiometricPunchLogForm(forms.ModelForm):
    class Meta:
        model = BiometricPunchLog
        fields = ['employee', 'punch_time', 'punch_type', 'device_terminal_id', 'verification_method', 'is_manual_override']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'punch_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'punch_type': forms.Select(attrs={'class': 'form-select'}),
            'device_terminal_id': forms.TextInput(attrs={'class': 'form-control'}),
            'verification_method': forms.Select(attrs={'class': 'form-select'}),
            'is_manual_override': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
