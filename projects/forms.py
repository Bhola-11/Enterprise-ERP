from django import forms
from .models import Project, Task, Timesheet, Milestone

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'code', 'client', 'project_manager', 'start_date', 'end_date', 'budget', 'status', 'priority', 'progress_percentage', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'project_manager': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'progress_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['project', 'milestone', 'title', 'assigned_to', 'status', 'priority', 'due_date', 'estimated_hours', 'description']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'milestone': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class TimesheetForm(forms.ModelForm):
    class Meta:
        model = Timesheet
        fields = ['task', 'date', 'hours', 'description', 'is_billable']
        widgets = {
            'task': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'is_billable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
