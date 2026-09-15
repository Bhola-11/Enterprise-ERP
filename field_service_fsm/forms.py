from django import forms
from decimal import Decimal
from .models import (
    ServiceTerritory, ServiceTechnician, WorkOrder, PartConsumption, CustomerSignoff
)
from sales.models import Customer
from inventory.models import Product

class WorkOrderCreateForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'customer', 'territory', 'assigned_technician', 'priority',
            'scheduled_start', 'scheduled_end', 'sla_deadline',
            'issue_summary', 'detailed_description', 'service_address'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'territory': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'assigned_technician': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'priority': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'type': 'datetime-local'}),
            'sla_deadline': forms.DateTimeInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'type': 'datetime-local'}),
            'issue_summary': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'detailed_description': forms.Textarea(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'rows': 3}),
            'service_address': forms.Textarea(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'rows': 2}),
        }


class PartConsumptionForm(forms.ModelForm):
    class Meta:
        model = PartConsumption
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'quantity': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
        }


class CustomerSignoffForm(forms.ModelForm):
    class Meta:
        model = CustomerSignoff
        fields = ['signatory_name', 'signatory_title', 'satisfaction_rating', 'feedback_notes']
        widgets = {
            'signatory_name': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'signatory_title': forms.TextInput(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'satisfaction_rating': forms.Select(choices=[(i, f"{i} Stars - Excellent" if i==5 else f"{i} Stars") for i in range(5, 0, -1)], attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm'}),
            'feedback_notes': forms.Textarea(attrs={'class': 'w-full rounded-lg border-slate-300 dark:border-slate-600 dark:bg-slate-700 text-sm', 'rows': 2}),
        }
