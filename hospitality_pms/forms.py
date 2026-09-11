from django import forms
from .models import (
    RoomType, HotelRoom, GuestProfile, RoomReservation,
    HousekeepingTask, FolioChargeLine
)

class GuestProfileForm(forms.ModelForm):
    class Meta:
        model = GuestProfile
        fields = ['first_name', 'last_name', 'email', 'phone', 'id_passport_number', 'nationality', 'vip_tier', 'special_preferences']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'id_passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'vip_tier': forms.Select(attrs={'class': 'form-select'}),
            'special_preferences': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RoomReservationForm(forms.ModelForm):
    class Meta:
        model = RoomReservation
        fields = ['guest', 'room_type', 'room', 'check_in_date', 'check_out_date', 'number_of_guests', 'nightly_rate', 'deposit_paid', 'booking_source', 'special_requests']
        widgets = {
            'guest': forms.Select(attrs={'class': 'form-select'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'check_in_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'number_of_guests': forms.NumberInput(attrs={'class': 'form-control'}),
            'nightly_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'deposit_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'booking_source': forms.Select(attrs={'class': 'form-select'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AddFolioChargeForm(forms.ModelForm):
    class Meta:
        model = FolioChargeLine
        fields = ['charge_type', 'description', 'amount']
        widgets = {
            'charge_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class HousekeepingTaskForm(forms.ModelForm):
    class Meta:
        model = HousekeepingTask
        fields = ['room', 'task_type', 'status', 'assigned_housekeeper', 'notes']
        widgets = {
            'room': forms.Select(attrs={'class': 'form-select'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_housekeeper': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
