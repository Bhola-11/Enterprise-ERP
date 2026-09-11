from django.contrib import admin
from .models import (
    MedicalDepartment, PractitionerDoctor, PatientRecord,
    AppointmentSchedule, ClinicalConsultationNote, PrescriptionOrder,
    PrescriptionMedicationItem, LaboratoryTestOrder, InpatientAdmission,
    MedicalBillingInvoice
)


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionMedicationItem
    extra = 1


@admin.register(MedicalDepartment)
class MedicalDepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'head_physician', 'floor_location', 'emergency_capable', 'is_active']
    search_fields = ['name', 'code']


@admin.register(PractitionerDoctor)
class PractitionerDoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'department', 'consultation_fee', 'room_number', 'is_active']
    list_filter = ['specialization', 'department', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'license_number']


@admin.register(PatientRecord)
class PatientRecordAdmin(admin.ModelAdmin):
    list_display = ['patient_mrn', 'first_name', 'last_name', 'gender', 'blood_group', 'date_of_birth', 'phone', 'created_at']
    list_filter = ['gender', 'blood_group']
    search_fields = ['patient_mrn', 'first_name', 'last_name', 'phone', 'insurance_policy_number']


@admin.register(AppointmentSchedule)
class AppointmentScheduleAdmin(admin.ModelAdmin):
    list_display = ['appointment_number', 'patient', 'doctor', 'department', 'scheduled_time', 'visit_type', 'token_number', 'status']
    list_filter = ['status', 'visit_type', 'department']
    search_fields = ['appointment_number', 'patient__first_name', 'patient__last_name']


@admin.register(ClinicalConsultationNote)
class ClinicalConsultationNoteAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'patient', 'doctor', 'assessment_icd10_code', 'assessment_diagnosis', 'created_at']
    search_fields = ['patient__first_name', 'patient__last_name', 'assessment_diagnosis']


@admin.register(PrescriptionOrder)
class PrescriptionOrderAdmin(admin.ModelAdmin):
    list_display = ['prescription_number', 'patient', 'doctor', 'status', 'created_at']
    list_filter = ['status']
    inlines = [PrescriptionItemInline]


@admin.register(LaboratoryTestOrder)
class LaboratoryTestOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'test_name', 'patient', 'doctor', 'sample_type', 'status', 'price', 'created_at']
    list_filter = ['status', 'sample_type']
    search_fields = ['order_number', 'test_name', 'patient__first_name']


@admin.register(InpatientAdmission)
class InpatientAdmissionAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'patient', 'admitting_doctor', 'ward_type', 'room_number', 'bed_number', 'admission_date', 'status']
    list_filter = ['status', 'ward_type']
    search_fields = ['admission_number', 'patient__first_name']


@admin.register(MedicalBillingInvoice)
class MedicalBillingInvoiceAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'patient', 'subtotal', 'insurance_covered_amount', 'patient_co_pay', 'grand_total', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['bill_number', 'patient__first_name']
