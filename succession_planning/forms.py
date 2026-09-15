from django import forms
from .models import CriticalRolePosition, TalentProfile, SuccessionPlan
from hr.models import Employee

class CriticalRolePositionForm(forms.ModelForm):
    class Meta:
        model = CriticalRolePosition
        fields = [
            'title', 'position_code', 'department', 'current_incumbent',
            'risk_of_vacancy', 'impact_of_loss', 'target_bench_strength',
            'required_competencies', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'position_code': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'current_incumbent': forms.Select(attrs={'class': 'form-select'}),
            'risk_of_vacancy': forms.Select(attrs={'class': 'form-select'}),
            'impact_of_loss': forms.Select(attrs={'class': 'form-select'}),
            'target_bench_strength': forms.NumberInput(attrs={'class': 'form-control'}),
            'required_competencies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TalentProfileForm(forms.ModelForm):
    class Meta:
        model = TalentProfile
        fields = [
            'employee', 'performance_rating', 'potential_rating', 'flight_risk',
            'retention_risk_reason', 'key_strengths', 'career_aspirations'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'performance_rating': forms.Select(attrs={'class': 'form-select'}),
            'potential_rating': forms.Select(attrs={'class': 'form-select'}),
            'flight_risk': forms.Select(attrs={'class': 'form-select'}),
            'retention_risk_reason': forms.TextInput(attrs={'class': 'form-control'}),
            'key_strengths': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'career_aspirations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SuccessionPlanForm(forms.ModelForm):
    class Meta:
        model = SuccessionPlan
        fields = [
            'critical_position', 'successor_employee', 'readiness_level',
            'ranking_priority', 'development_needs', 'status'
        ]
        widgets = {
            'critical_position': forms.Select(attrs={'class': 'form-select'}),
            'successor_employee': forms.Select(attrs={'class': 'form-select'}),
            'readiness_level': forms.Select(attrs={'class': 'form-select'}),
            'ranking_priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'development_needs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
