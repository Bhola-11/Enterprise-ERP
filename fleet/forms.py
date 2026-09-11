from django import forms
from .models import Vehicle, Driver, FuelLog, TripRecord

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = '__all__'
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'vin': forms.TextInput(attrs={'class': 'form-control'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'current_odometer_km': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_driver': forms.Select(attrs={'class': 'form-select'}),
            'insurance_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class FuelLogForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = ['vehicle', 'date', 'liters', 'cost_per_liter', 'odometer_km', 'station']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'liters': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost_per_liter': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'odometer_km': forms.NumberInput(attrs={'class': 'form-control'}),
            'station': forms.TextInput(attrs={'class': 'form-control'}),
        }
