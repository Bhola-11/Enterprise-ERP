from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db import transaction
from .models import (
    PatientRecord, PractitionerDoctor, AppointmentSchedule,
    ClinicalConsultationNote, PrescriptionOrder, PrescriptionMedicationItem,
    LaboratoryTestOrder, InpatientAdmission, MedicalBillingInvoice
)
from accounting.models import JournalEntry, JournalItem, Account


class ClinicalTriageService:
    """
    Automated Clinical Decision Support & Triage Service.
    Evaluates patient vital signs, flags abnormal ranges, and checks drug allergy interactions.
    """

    @staticmethod
    def assess_vital_signs(systolic, diastolic, heart_rate, temp_f, spo2):
        alerts = []
        triage_level = 'STANDARD'

        if spo2 < 92:
            alerts.append(f"CRITICAL: Low Oxygen Saturation ({spo2}% SpO2) - Immediate Oxygen Therapy Required")
            triage_level = 'EMERGENCY'
        elif spo2 < 95:
            alerts.append(f"WARNING: Borderline SpO2 ({spo2}%)")

        if systolic >= 180 or diastolic >= 120:
            alerts.append(f"CRITICAL: Hypertensive Crisis ({systolic}/{diastolic} mmHg)")
            triage_level = 'EMERGENCY'
        elif systolic >= 140 or diastolic >= 90:
            alerts.append(f"WARNING: Stage 2 Hypertension ({systolic}/{diastolic} mmHg)")

        if temp_f >= 103.0:
            alerts.append(f"HIGH FEVER: Temperature {temp_f}°F - Antipyretic & Cooling Protocol")
            if triage_level != 'EMERGENCY':
                triage_level = 'URGENT'

        if heart_rate > 120 or heart_rate < 50:
            alerts.append(f"CARDIAC WARNING: Abnormal Pulse ({heart_rate} BPM)")
            if triage_level != 'EMERGENCY':
                triage_level = 'URGENT'

        return {
            'triage_level': triage_level,
            'alerts': alerts,
            'is_critical': triage_level == 'EMERGENCY'
        }

    @staticmethod
    def check_drug_allergy_conflict(patient, drug_name):
        """
        Cross-checks prescribed medication against patient known allergy notes.
        """
        allergies = (patient.allergy_notes or '').lower()
        drug = drug_name.lower()

        if not allergies:
            return {'has_conflict': False, 'message': 'No known allergies recorded.'}

        known_allergens = [a.strip() for a in allergies.split(',') if a.strip()]
        for allergen in known_allergens:
            if allergen in drug or drug in allergen:
                return {
                    'has_conflict': True,
                    'message': f"ALLERGY WARNING: Patient has recorded allergy to '{allergen}'. Prescribing '{drug_name}' may cause adverse reaction!"
                }

        return {'has_conflict': False, 'message': 'No allergy conflict detected.'}


class DoctorRosteringEngine:
    """
    Hospital appointment scheduling and outpatient queue token management.
    """

    @staticmethod
    def book_appointment(patient, doctor, department, scheduled_time, visit_type='OPD', chief_complaint=""):
        # Check collision for doctor within 15 minutes window
        existing = AppointmentSchedule.objects.filter(
            doctor=doctor,
            scheduled_time__range=[
                scheduled_time - timezone.timedelta(minutes=14),
                scheduled_time + timezone.timedelta(minutes=14)
            ],
            status__in=['SCHEDULED', 'CHECKED_IN', 'IN_CONSULTATION']
        ).first()

        if existing:
            raise ValueError(f"Dr. {doctor.user.last_name} already has an appointment scheduled at this time slot.")

        # Calculate daily token sequence
        today_start = scheduled_time.replace(hour=0, minute=0, second=0)
        today_end = scheduled_time.replace(hour=23, minute=59, second=59)
        tokens_today = AppointmentSchedule.objects.filter(
            doctor=doctor,
            scheduled_time__range=[today_start, today_end]
        ).count()
        next_token = tokens_today + 1

        appt_num = f"APT-{doctor.department.code}-{timezone.now().strftime('%Y%m%d')}-{next_token:03d}"

        appt = AppointmentSchedule.objects.create(
            appointment_number=appt_num,
            patient=patient,
            doctor=doctor,
            department=department,
            scheduled_time=scheduled_time,
            visit_type=visit_type,
            token_number=next_token,
            chief_complaint=chief_complaint,
            status='SCHEDULED'
        )

        return appt


class MedicalBillingService:
    """
    Collation of hospital OPD and IPD charges, insurance split calculations,
    and automatic General Ledger revenue recognition.
    """

    @classmethod
    @transaction.atomic
    def generate_encounter_bill(cls, patient, appointment=None, admission=None, additional_lab_orders=None, additional_medications_cost=Decimal('0.00'), user=None):
        consult_charges = Decimal('0.00')
        lab_charges = Decimal('0.00')
        pharmacy_charges = Decimal(str(additional_medications_cost))
        room_charges = Decimal('0.00')

        if appointment:
            consult_charges = appointment.doctor.consultation_fee

        if additional_lab_orders:
            for lab in additional_lab_orders:
                lab_charges += lab.price

        if admission:
            days = 1
            if admission.discharge_date and admission.admission_date:
                days = max(1, (admission.discharge_date.date() - admission.admission_date.date()).days)
            room_charges = admission.daily_bed_rate * Decimal(days)

        subtotal = consult_charges + lab_charges + pharmacy_charges + room_charges
        tax_amount = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # 5% healthcare service tax
        gross_total = subtotal + tax_amount

        # Insurance Co-Pay calculation: 80% insurance / 20% patient if policy present
        if patient.insurance_policy_number:
            insurance_amt = (gross_total * Decimal('0.80')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            patient_copay = gross_total - insurance_amt
        else:
            insurance_amt = Decimal('0.00')
            patient_copay = gross_total

        bill_num = f"MED-BILL-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        bill = MedicalBillingInvoice.objects.create(
            bill_number=bill_num,
            patient=patient,
            appointment=appointment,
            admission=admission,
            consultation_charges=consult_charges,
            lab_charges=lab_charges,
            pharmacy_charges=pharmacy_charges,
            room_charges=room_charges,
            subtotal=subtotal,
            tax_amount=tax_amount,
            insurance_covered_amount=insurance_amt,
            patient_co_pay=patient_copay,
            grand_total=gross_total,
            status='PENDING'
        )

        # GL Journal Posting
        cls.post_medical_bill_to_gl(bill, user)

        return bill

    @classmethod
    def post_medical_bill_to_gl(cls, bill, user=None):
        try:
            ar_account = Account.objects.filter(account_type='ASSET', name__icontains='Receivable').first()
            revenue_account = Account.objects.filter(account_type='REVENUE').first()

            if not (ar_account and revenue_account):
                return None

            je = JournalEntry.objects.create(
                entry_number=f"JE-MED-{bill.bill_number}",
                date=timezone.now().date(),
                reference=f"Medical Bill: {bill.bill_number}",
                narration=f"Hospital encounter revenue for patient {bill.patient.full_name}",
                total_debit=bill.grand_total,
                total_credit=bill.grand_total,
                status='POSTED',
                created_by=user
            )

            # Debit Accounts Receivable
            JournalItem.objects.create(
                journal_entry=je,
                account=ar_account,
                debit=bill.grand_total,
                credit=Decimal('0.00'),
                description=f"Patient AR / Co-Pay {bill.bill_number}"
            )

            # Credit Hospital Revenue
            JournalItem.objects.create(
                journal_entry=je,
                account=revenue_account,
                debit=Decimal('0.00'),
                credit=bill.grand_total,
                description=f"Healthcare clinical & diagnostic revenue"
            )

            return je
        except Exception:
            return None
