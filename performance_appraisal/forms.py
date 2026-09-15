from django import forms
from .models import AppraisalCycle, CompetencyFramework, AppraisalSubmission, ContinuousFeedbackNote

class AppraisalCycleForm(forms.ModelForm):
    class Meta:
        model = AppraisalCycle
        fields = ['name', 'cycle_type', 'start_date', 'end_date', 'self_review_deadline', 'manager_review_deadline', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'cycle_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'self_review_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'manager_review_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class AppraisalSubmissionForm(forms.ModelForm):
    class Meta:
        model = AppraisalSubmission
        fields = ['self_rating', 'self_summary', 'peer_average_rating', 'manager_rating', 'manager_summary', 'status']
        widgets = {
            'self_rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '1', 'max': '5'}),
            'self_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'peer_average_rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '1', 'max': '5'}),
            'manager_rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '1', 'max': '5'}),
            'manager_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class ContinuousFeedbackNoteForm(forms.ModelForm):
    class Meta:
        model = ContinuousFeedbackNote
        fields = ['employee', 'giver', 'feedback_type', 'title', 'content', 'is_private_manager']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'giver': forms.Select(attrs={'class': 'form-select'}),
            'feedback_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_private_manager': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
