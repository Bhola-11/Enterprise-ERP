from django import forms
from .models import BillOfMaterials, BOMItem, ProductionOrder, WorkCenter, QualityInspection

class BOMForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterials
        fields = ['bom_number', 'finished_product', 'quantity', 'is_active', 'notes']
        widgets = {
            'bom_number': forms.TextInput(attrs={'class': 'form-control'}),
            'finished_product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ['order_number', 'bom', 'work_center', 'quantity_to_produce', 'start_date', 'due_date']
        widgets = {
            'order_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bom': forms.Select(attrs={'class': 'form-select'}),
            'work_center': forms.Select(attrs={'class': 'form-select'}),
            'quantity_to_produce': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
