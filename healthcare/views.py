import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.db.models import Count, Sum, Q

from .models import (
    MedicalDepartment, PractitionerDoctor, PatientRecord,
    AppointmentSchedule, ClinicalConsultationNote, PrescriptionOrder,
    PrescriptionMedicationItem, LaboratoryTestOrder, InpatientAdmission,
    MedicalBillingInvoice
)
from .forms import (
    PatientRegistrationForm, AppointmentBookingForm, ClinicalConsultationForm,
    LaboratoryOrderForm, InpatientAdmissionForm
)
from .services import ClinicalTriageService, DoctorRosteringEngine, MedicalBillingService


@login_required
def healthcare_dashboard(request):
    total_patients = PatientRecord.objects.count()
    today_start = timezone.now().replace(hour=0, minute=0, second=0)
    today_end = timezone.now().replace(hour=23, minute=59, second=59)

    today_appointments = AppointmentSchedule.objects.filter(scheduled_time__range=[today_start, today_end]).select_related('patient', 'doctor', 'department').order_by('token_number')
    active_inpatient = InpatientAdmission.objects.filter(status='ADMITTED').select_related('patient', 'admitting_doctor')
    pending_labs = LaboratoryTestOrder.objects.filter(status__in=['ORDERED', 'SAMPLE_COLLECTED', 'IN_ANALYSIS']).count()
    doctors_count = PractitionerDoctor.objects.filter(is_active=True).count()

    context = {
        'total_patients': total_patients,
        'today_appointments': today_appointments,
        'today_appt_count': today_appointments.count(),
        'active_inpatient': active_inpatient,
        'inpatient_count': active_inpatient.count(),
        'pending_labs': pending_labs,
        'doctors_count': doctors_count,
        'page_title': 'Hospital EMR & Clinical Operations',
    }
    return render(request, 'healthcare/dashboard.html', context)


@login_required
def patient_list(request):
    query = request.GET.get('q', '').strip()
    patients = PatientRecord.objects.all().order_by('-created_at')
    if query:
        patients = patients.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(patient_mrn__icontains=query) |
            Q(phone__icontains=query)
        )

    return render(request, 'healthcare/patient_list.html', {
        'patients': patients[:100],
        'query': query,
        'page_title': 'Patient Master EMR Directory'
    })


@login_required
def patient_create(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f"Patient {patient.full_name} registered successfully (MRN: {patient.patient_mrn[:8]}).")
            return redirect('healthcare:patient_detail', pk=patient.id)
    else:
        form = PatientRegistrationForm()

    return render(request, 'healthcare/patient_form.html', {'form': form, 'page_title': 'Register New Patient'})


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(PatientRecord, pk=pk)
    appointments = patient.appointments.select_related('doctor', 'department').order_by('-scheduled_time')
    clinical_notes = patient.clinical_notes.select_related('doctor', 'appointment').order_by('-created_at')
    prescriptions = patient.prescriptions.prefetch_related('medications').order_by('-created_at')
    lab_orders = patient.lab_orders.select_related('doctor').order_by('-created_at')
    admissions = patient.admissions.select_related('admitting_doctor').order_by('-admission_date')
    bills = patient.medical_bills.order_by('-created_at')

    return render(request, 'healthcare/patient_detail.html', {
        'patient': patient,
        'appointments': appointments,
        'clinical_notes': clinical_notes,
        'prescriptions': prescriptions,
        'lab_orders': lab_orders,
        'admissions': admissions,
        'bills': bills,
        'page_title': f'Patient EMR Chart - {patient.full_name}'
    })


@login_required
def appointment_list(request):
    today = timezone.now().date()
    appointments = AppointmentSchedule.objects.select_related('patient', 'doctor', 'department').order_by('-scheduled_time')
    return render(request, 'healthcare/appointment_list.html', {
        'appointments': appointments[:100],
        'page_title': 'Doctor Appointment Scheduling'
    })


@login_required
def appointment_book(request):
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            try:
                appt = DoctorRosteringEngine.book_appointment(
                    patient=form.cleaned_data['patient'],
                    doctor=form.cleaned_data['doctor'],
                    department=form.cleaned_data['department'],
                    scheduled_time=form.cleaned_data['scheduled_time'],
                    visit_type=form.cleaned_data['visit_type'],
                    chief_complaint=form.cleaned_data['chief_complaint']
                )
                messages.success(request, f"Appointment #{appt.token_number} booked successfully for {appt.patient.full_name} with Dr. {appt.doctor.user.last_name}.")
                return redirect('healthcare:appointment_list')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = AppointmentBookingForm()

    return render(request, 'healthcare/appointment_form.html', {'form': form, 'page_title': 'Book Doctor Appointment'})


@login_required
def consultation_create(request, appointment_id):
    appointment = get_object_or_404(
        AppointmentSchedule.objects.select_related('patient', 'doctor', 'department'),
        pk=appointment_id
    )

    if request.method == 'POST':
        form = ClinicalConsultationForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.appointment = appointment
            note.patient = appointment.patient
            note.doctor = appointment.doctor
            note.save()

            appointment.status = 'COMPLETED'
            appointment.save(update_fields=['status'])

            messages.success(request, f"Clinical consultation note saved for {appointment.patient.full_name}.")
            return redirect('healthcare:patient_detail', pk=appointment.patient.id)
    else:
        form = ClinicalConsultationForm(initial={
            'subjective_symptoms': appointment.chief_complaint
        })

    return render(request, 'healthcare/consultation_form.html', {
        'form': form,
        'appointment': appointment,
        'patient': appointment.patient,
        'page_title': f'Clinical Encounter (SOAP) - {appointment.patient.full_name}'
    })


@login_required
def lab_order_list(request):
    orders = LaboratoryTestOrder.objects.select_related('patient', 'doctor').order_by('-created_at')
    return render(request, 'healthcare/lab_order_list.html', {
        'orders': orders[:100],
        'page_title': 'Hospital Diagnostic Pathology & Labs'
    })


@login_required
def lab_order_create(request):
    if request.method == 'POST':
        form = LaboratoryOrderForm(request.POST)
        if form.is_valid():
            lab = form.save(commit=False)
            lab.specimen_barcode = f"LAB-{timezone.now().strftime('%y%m%d%H%M%S')}"
            lab.save()
            messages.success(request, f"Lab order #{lab.order_number[:8]} ({lab.test_name}) created successfully.")
            return redirect('healthcare:lab_order_list')
    else:
        form = LaboratoryOrderForm()

    return render(request, 'healthcare/lab_order_form.html', {'form': form, 'page_title': 'Order Diagnostic Lab Test'})


@login_required
def inpatient_list(request):
    admissions = InpatientAdmission.objects.select_related('patient', 'admitting_doctor').order_by('-admission_date')
    return render(request, 'healthcare/inpatient_list.html', {
        'admissions': admissions,
        'page_title': 'Inpatient Ward & Bed Occupancy (IPD)'
    })


@login_required
def inpatient_admit(request):
    if request.method == 'POST':
        form = InpatientAdmissionForm(request.POST)
        if form.is_valid():
            adm = form.save()
            messages.success(request, f"Patient {adm.patient.full_name} admitted to {adm.get_ward_type_display()} ({adm.room_number}).")
            return redirect('healthcare:inpatient_list')
    else:
        form = InpatientAdmissionForm()

    return render(request, 'healthcare/inpatient_form.html', {'form': form, 'page_title': 'Admit Inpatient'})


@login_required
def billing_list(request):
    bills = MedicalBillingInvoice.objects.select_related('patient', 'appointment').order_by('-created_at')
    return render(request, 'healthcare/billing_list.html', {
        'bills': bills,
        'page_title': 'Hospital Encounters & Medical Invoices'
    })


@login_required
def billing_generate(request, patient_id):
    patient = get_object_or_404(PatientRecord, pk=patient_id)
    latest_appt = patient.appointments.filter(status='COMPLETED').order_by('-scheduled_time').first()
    latest_admission = patient.admissions.filter(status='ADMITTED').first()
    unbilled_labs = patient.lab_orders.filter(status='COMPLETED')

    bill = MedicalBillingService.generate_encounter_bill(
        patient=patient,
        appointment=latest_appt,
        admission=latest_admission,
        additional_lab_orders=unbilled_labs,
        user=request.user
    )
    messages.success(request, f"Medical bill #{bill.bill_number} generated for ${bill.grand_total:,.2f}.")
    return redirect('healthcare:patient_detail', pk=patient.id)


# ---------------- API Endpoints ----------------

@login_required
@require_GET
def api_vital_signs_assess(request):
    sys = int(request.GET.get('sys', 120))
    dia = int(request.GET.get('dia', 80))
    hr = int(request.GET.get('hr', 72))
    temp = float(request.GET.get('temp', 98.6))
    spo2 = int(request.GET.get('spo2', 98))

    res = ClinicalTriageService.assess_vital_signs(sys, dia, hr, temp, spo2)
    return JsonResponse({'success': True, 'data': res})


@login_required
@require_GET
def api_check_drug_allergy(request):
    patient_id = request.GET.get('patient_id')
    drug = request.GET.get('drug_name', '')
    patient = get_object_or_404(PatientRecord, pk=patient_id)

    res = ClinicalTriageService.check_drug_allergy_conflict(patient, drug)
    return JsonResponse({'success': True, 'data': res})
