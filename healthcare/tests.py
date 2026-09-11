from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from healthcare.models import (
    MedicalDepartment, PractitionerDoctor, PatientRecord,
    AppointmentSchedule, LaboratoryTestOrder, InpatientAdmission
)
from healthcare.services import ClinicalTriageService, DoctorRosteringEngine, MedicalBillingService

User = get_user_model()


class HealthcareTestCase(TestCase):
    def setUp(self):
        self.dept = MedicalDepartment.objects.create(name="Cardiology", code="CARD-01")
        self.doc_user = User.objects.create_user(username="dr_smith", email="smith@hospital.io", password="Password@123", role="STAFF", first_name="John", last_name="Smith")
        self.doctor = PractitionerDoctor.objects.create(
            user=self.doc_user,
            license_number="MD-987654",
            specialization="Cardiologist",
            department=self.dept,
            consultation_fee=Decimal('150.00')
        )

        self.patient = PatientRecord.objects.create(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=timezone.now().date() - timezone.timedelta(days=365*30),
            gender="FEMALE",
            blood_group="O+",
            phone="555-0199",
            allergy_notes="Penicillin, Sulfa drugs",
            insurance_provider="BlueCross Health",
            insurance_policy_number="BC-88992211"
        )

    def test_vital_signs_triage_assessment(self):
        # Emergency low SpO2 & high BP
        res_critical = ClinicalTriageService.assess_vital_signs(
            systolic=190, diastolic=125, heart_rate=130, temp_f=103.5, spo2=89
        )
        self.assertEqual(res_critical['triage_level'], 'EMERGENCY')
        self.assertTrue(res_critical['is_critical'])
        self.assertTrue(len(res_critical['alerts']) >= 3)

        # Normal vitals
        res_normal = ClinicalTriageService.assess_vital_signs(
            systolic=120, diastolic=80, heart_rate=72, temp_f=98.6, spo2=99
        )
        self.assertEqual(res_normal['triage_level'], 'STANDARD')
        self.assertFalse(res_normal['is_critical'])

    def test_drug_allergy_conflict_detection(self):
        # Prescribing Penicillin -> conflict
        conflict = ClinicalTriageService.check_drug_allergy_conflict(self.patient, "Amoxicillin / Penicillin V")
        self.assertTrue(conflict['has_conflict'])
        self.assertIn("ALLERGY WARNING", conflict['message'])

        # Prescribing Paracetamol -> safe
        safe = ClinicalTriageService.check_drug_allergy_conflict(self.patient, "Acetaminophen 500mg")
        self.assertFalse(safe['has_conflict'])

    def test_doctor_rostering_and_slot_booking(self):
        appt_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        appt1 = DoctorRosteringEngine.book_appointment(
            patient=self.patient,
            doctor=self.doctor,
            department=self.dept,
            scheduled_time=appt_time,
            chief_complaint="Chest discomfort and fatigue"
        )
        self.assertEqual(appt1.token_number, 1)
        self.assertEqual(appt1.status, 'SCHEDULED')

        # Booking same time slot -> should raise ValueError (collision)
        with self.assertRaises(ValueError):
            DoctorRosteringEngine.book_appointment(
                patient=self.patient,
                doctor=self.doctor,
                department=self.dept,
                scheduled_time=appt_time + timezone.timedelta(minutes=5),
                chief_complaint="Collision test"
            )

    def test_medical_billing_and_insurance_copay(self):
        lab = LaboratoryTestOrder.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            test_code="LIPID-01",
            test_name="Lipid Profile",
            price=Decimal('50.00'),
            status='COMPLETED'
        )

        bill = MedicalBillingService.generate_encounter_bill(
            patient=self.patient,
            appointment=None,
            admission=None,
            additional_lab_orders=[lab],
            additional_medications_cost=Decimal('50.00'),
            user=self.doc_user
        )

        # Subtotal: 50 (lab) + 50 (meds) = 100. Tax 5% = 5. Gross = 105
        self.assertEqual(bill.subtotal, Decimal('100.00'))
        self.assertEqual(bill.tax_amount, Decimal('5.00'))
        self.assertEqual(bill.grand_total, Decimal('105.00'))

        # Insurance 80% of 105 = 84.00, Patient Co-pay 20% = 21.00
        self.assertEqual(bill.insurance_covered_amount, Decimal('84.00'))
        self.assertEqual(bill.patient_co_pay, Decimal('21.00'))
