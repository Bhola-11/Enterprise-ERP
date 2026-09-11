from django import forms
from .models import (
    InspectionPlan, InspectionCharacteristic, QualityInspectionTicket,
    NonConformanceReport, CAPAAction
)

class InspectionPlanForm(forms.ModelForm):
    class Meta:
        model = InspectionPlan
        fields = ['code', 'name', 'category', 'sampling_standard', 'is_active', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'sampling_standard': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class InspectionTicketCreateForm(forms.ModelForm):
    class Meta:
        model = QualityInspectionTicket
        fields = ['plan', 'reference_type', 'reference_code', 'lot_size', 'inspection_date']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'reference_type': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_code': forms.TextInput(attrs={'class': 'form-control'}),
            'lot_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'inspection_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class InspectionVerdictForm(forms.Form):
    accepted_quantity = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    rejected_quantity = forms.IntegerField(initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    inspector_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))


class NonConformanceReportForm(forms.ModelForm):
    class Meta:
        model = NonConformanceReport
        fields = ['defect_title', 'defect_severity', 'defect_description', 'root_cause_analysis', 'containment_action', 'status']
        widgets = {
            'defect_title': forms.TextInput(attrs={'class': 'form-control'}),
            'defect_severity': forms.Select(attrs={'class': 'form-select'}),
            'defect_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'root_cause_analysis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'containment_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class CAPAActionForm(forms.ModelForm):
    class Meta:
        model = CAPAAction
        fields = ['action_type', 'action_description', 'assigned_owner', 'target_due_date', 'verification_evidence', 'is_verified']
        widgets = {
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'action_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_owner': forms.TextInput(attrs={'class': 'form-control'}),
            'target_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'verification_evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
