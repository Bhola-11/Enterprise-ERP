from django import forms
from .models import (
    PatientRecord, PractitionerDoctor, AppointmentSchedule,
    ClinicalConsultationNote, PrescriptionOrder, PrescriptionMedicationItem,
    LaboratoryTestOrder, InpatientAdmission
)


class PatientRegistrationForm(forms.ModelForm):
    class Meta:
        model = PatientRecord
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'blood_group',
            'phone', 'email', 'address', 'city', 'emergency_contact_name',
            'emergency_contact_phone', 'insurance_provider', 'insurance_policy_number',
            'allergy_notes', 'chronic_conditions'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_provider': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_policy_number': forms.TextInput(attrs={'class': 'form-control'}),
            'allergy_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Penicillin, Sulfa drugs, Peanuts'}),
            'chronic_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Hypertension, Asthma, Type 2 Diabetes'}),
        }


class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = AppointmentSchedule
        fields = ['patient', 'doctor', 'department', 'scheduled_time', 'visit_type', 'chief_complaint']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'visit_type': forms.Select(attrs={'class': 'form-select'}),
            'chief_complaint': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Primary symptoms described by patient...'}),
        }


class ClinicalConsultationForm(forms.ModelForm):
    class Meta:
        model = ClinicalConsultationNote
        fields = [
            'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate_bpm',
            'temperature_f', 'respiratory_rate', 'spo2_percentage', 'weight_kg',
            'subjective_symptoms', 'objective_exam', 'assessment_icd10_code',
            'assessment_diagnosis', 'treatment_plan', 'follow_up_date'
        ]
        widgets = {
            'blood_pressure_systolic': forms.NumberInput(attrs={'class': 'form-control text-center font-monospace'}),
            'blood_pressure_diastolic': forms.NumberInput(attrs={'class': 'form-control text-center font-monospace'}),
            'heart_rate_bpm': forms.NumberInput(attrs={'class': 'form-control text-center font-monospace'}),
            'temperature_f': forms.NumberInput(attrs={'class': 'form-control text-center font-monospace', 'step': '0.1'}),
            'respiratory_rate': forms.NumberInput(attrs={'class': 'form-control text-center font-monospace'}),
            'spo2_percentage': forms.NumberInput(attrs={'class': 'form-control text-center font-monospace'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control text-center font-monospace', 'step': '0.1'}),
            'subjective_symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'objective_exam': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assessment_icd10_code': forms.TextInput(attrs={'class': 'form-control font-monospace', 'placeholder': 'e.g. J06.9, I10'}),
            'assessment_diagnosis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Acute Upper Respiratory Tract Infection'}),
            'treatment_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class LaboratoryOrderForm(forms.ModelForm):
    class Meta:
        model = LaboratoryTestOrder
        fields = ['patient', 'doctor', 'test_code', 'test_name', 'sample_type', 'price']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'test_code': forms.TextInput(attrs={'class': 'form-control font-monospace'}),
            'test_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sample_type': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class InpatientAdmissionForm(forms.ModelForm):
    class Meta:
        model = InpatientAdmission
        fields = ['patient', 'admitting_doctor', 'ward_type', 'room_number', 'bed_number', 'daily_bed_rate', 'admission_date', 'admission_reason']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'admitting_doctor': forms.Select(attrs={'class': 'form-select'}),
            'ward_type': forms.Select(attrs={'class': 'form-select'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bed_number': forms.TextInput(attrs={'class': 'form-control'}),
            'daily_bed_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'admission_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'admission_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
