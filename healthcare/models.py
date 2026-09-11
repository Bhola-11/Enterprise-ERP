from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


class MedicalDepartment(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    head_physician = models.CharField(max_length=150, blank=True)
    floor_location = models.CharField(max_length=100, default='Floor 1, Wing A')
    emergency_capable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Medical Department'
        verbose_name_plural = 'Medical Departments'

    def __str__(self):
        return f"{self.name} ({self.code})"


class PractitionerDoctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    license_number = models.CharField(max_length=100, unique=True)
    specialization = models.CharField(max_length=150, default='General Physician')
    department = models.ForeignKey(MedicalDepartment, on_delete=models.PROTECT, related_name='doctors')
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('75.00'))
    qualifications = models.CharField(max_length=255, default='MBBS, MD')
    room_number = models.CharField(max_length=50, default='Consultation Room 101')
    available_days = models.CharField(max_length=100, default='Mon, Tue, Wed, Thu, Fri')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['user__first_name', 'specialization']
        verbose_name = 'Practitioner Doctor'
        verbose_name_plural = 'Practitioner Doctors'

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username} ({self.specialization})"


class PatientRecord(models.Model):
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other / Non-Binary'),
    ]

    BLOOD_GROUPS = [
        ('A+', 'A Positive (A+)'),
        ('A-', 'A Negative (A-)'),
        ('B+', 'B Positive (B+)'),
        ('B-', 'B Negative (B-)'),
        ('AB+', 'AB Positive (AB+)'),
        ('AB-', 'AB Negative (AB-)'),
        ('O+', 'O Positive (O+)'),
        ('O-', 'O Negative (O-)'),
        ('UNKNOWN', 'Unknown / Not Tested'),
    ]

    patient_mrn = models.CharField(max_length=50, unique=True, default=uuid.uuid4, help_text="Medical Record Number")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='MALE')
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUPS, default='O+')
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    insurance_provider = models.CharField(max_length=150, blank=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True)
    allergy_notes = models.TextField(blank=True, help_text="Known drug, food, or environmental allergies (e.g. Penicillin)")
    chronic_conditions = models.TextField(blank=True, help_text="Known chronic conditions (e.g. Type 2 Diabetes, Hypertension)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Patient Medical Record (EMR)'
        verbose_name_plural = 'Patient Medical Records (EMR)'

    def __str__(self):
        return f"[{self.patient_mrn[:8]}] {self.first_name} {self.last_name} ({self.gender}, {self.blood_group})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class AppointmentSchedule(models.Model):
    VISIT_TYPES = [
        ('OPD', 'Outpatient Consultation (OPD)'),
        ('FOLLOW_UP', 'Routine Follow-Up Review'),
        ('EMERGENCY', 'Emergency Triage'),
        ('TELECONSULT', 'Telemedicine Remote Consult'),
    ]

    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled / Confirmed'),
        ('CHECKED_IN', 'Patient Arrived & Checked-In'),
        ('IN_CONSULTATION', 'In-Consultation with Physician'),
        ('COMPLETED', 'Completed & Prescribed'),
        ('CANCELLED', 'Cancelled / No-Show'),
    ]

    appointment_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    patient = models.ForeignKey(PatientRecord, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(PractitionerDoctor, on_delete=models.PROTECT, related_name='appointments')
    department = models.ForeignKey(MedicalDepartment, on_delete=models.PROTECT, related_name='appointments')
    scheduled_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=20)
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPES, default='OPD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    token_number = models.PositiveIntegerField(default=1)
    chief_complaint = models.TextField(help_text="Primary symptoms or reason for visit")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_time']
        verbose_name = 'Doctor Appointment Schedule'
        verbose_name_plural = 'Doctor Appointment Schedules'

    def __str__(self):
        return f"Appt #{self.token_number} - {self.patient.full_name} with Dr. {self.doctor.user.last_name} ({self.status})"


class ClinicalConsultationNote(models.Model):
    appointment = models.OneToOneField(AppointmentSchedule, on_delete=models.CASCADE, related_name='clinical_note')
    patient = models.ForeignKey(PatientRecord, on_delete=models.CASCADE, related_name='clinical_notes')
    doctor = models.ForeignKey(PractitionerDoctor, on_delete=models.PROTECT, related_name='clinical_notes')

    # Vital Signs
    blood_pressure_systolic = models.PositiveIntegerField(default=120)
    blood_pressure_diastolic = models.PositiveIntegerField(default=80)
    heart_rate_bpm = models.PositiveIntegerField(default=72)
    temperature_f = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('98.6'))
    respiratory_rate = models.PositiveIntegerField(default=16)
    spo2_percentage = models.PositiveIntegerField(default=98)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('70.00'))

    # SOAP Clinical Notes
    subjective_symptoms = models.TextField(help_text="Patient reported symptoms and history of present illness")
    objective_exam = models.TextField(help_text="Physician physical examination findings")
    assessment_icd10_code = models.CharField(max_length=20, blank=True, help_text="ICD-10 Diagnostic Code (e.g. J06.9)")
    assessment_diagnosis = models.CharField(max_length=255, help_text="Clinical diagnosis")
    treatment_plan = models.TextField(help_text="Physician treatment orders, advice, diet, therapy")
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Clinical Consultation Note'
        verbose_name_plural = 'Clinical Consultation Notes'

    def __str__(self):
        return f"EMR Note: {self.patient.full_name} - {self.assessment_diagnosis} ({self.created_at.strftime('%d/%m/%Y')})"


class PrescriptionOrder(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active / Pending Pharmacy'),
        ('DISPENSED', 'Dispensed by Pharmacy'),
        ('CANCELLED', 'Cancelled'),
    ]

    prescription_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    consultation = models.ForeignKey(ClinicalConsultationNote, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(PatientRecord, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(PractitionerDoctor, on_delete=models.PROTECT, related_name='prescriptions')
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    dispensed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prescription Order'
        verbose_name_plural = 'Prescription Orders'

    def __str__(self):
        return f"Rx #{self.prescription_number[:8]} - {self.patient.full_name} ({self.status})"


class PrescriptionMedicationItem(models.Model):
    DOSAGE_FORMS = [
        ('TABLET', 'Tablet'),
        ('CAPSULE', 'Capsule'),
        ('SYRUP', 'Oral Liquid / Syrup'),
        ('INJECTION', 'Injection (IV/IM)'),
        ('INHALER', 'Inhaler / Nebulizer'),
        ('OINTMENT', 'Topical Ointment / Cream'),
        ('DROPS', 'Eye / Ear Drops'),
    ]

    FREQUENCIES = [
        ('QD', 'Once Daily (QD)'),
        ('BID', 'Twice Daily (BID - 12h)'),
        ('TID', 'Three Times Daily (TID - 8h)'),
        ('QID', 'Four Times Daily (QID - 6h)'),
        ('PRN', 'As Needed (PRN / SOS)'),
        ('STAT', 'Immediately (STAT Single Dose)'),
    ]

    FOOD_INSTRUCTIONS = [
        ('AFTER_FOOD', 'After Meals'),
        ('BEFORE_FOOD', 'Before Meals / Empty Stomach'),
        ('WITH_FOOD', 'With Meals / Food'),
        ('BEDTIME', 'At Bedtime'),
    ]

    prescription = models.ForeignKey(PrescriptionOrder, on_delete=models.CASCADE, related_name='medications')
    medicine_name = models.CharField(max_length=200, help_text="Generic or Brand Drug Name (e.g. Amoxicillin + Clavulanic Acid 625mg)")
    dosage_strength = models.CharField(max_length=50, default='500 mg')
    dosage_form = models.CharField(max_length=20, choices=DOSAGE_FORMS, default='TABLET')
    frequency = models.CharField(max_length=10, choices=FREQUENCIES, default='BID')
    duration_days = models.PositiveIntegerField(default=5)
    food_instruction = models.CharField(max_length=20, choices=FOOD_INSTRUCTIONS, default='AFTER_FOOD')
    quantity_prescribed = models.PositiveIntegerField(default=10)
    special_notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Prescription Medication Item'
        verbose_name_plural = 'Prescription Medication Items'

    def __str__(self):
        return f"{self.medicine_name} - {self.frequency} x {self.duration_days} days"


class LaboratoryTestOrder(models.Model):
    STATUS_CHOICES = [
        ('ORDERED', 'Ordered / Pending Sample Collection'),
        ('SAMPLE_COLLECTED', 'Sample Collected & Barcoded'),
        ('IN_ANALYSIS', 'In-Analysis / Processing in Lab'),
        ('COMPLETED', 'Completed & Verified by Pathologist'),
        ('CANCELLED', 'Cancelled'),
    ]

    SAMPLE_TYPES = [
        ('BLOOD', 'Whole Blood / Serum / Plasma'),
        ('URINE', 'Urine Sample'),
        ('SWAB', 'Nasopharyngeal / Throat Swab'),
        ('BIOPSY', 'Tissue / Biopsy Specimen'),
        ('STOOL', 'Stool Sample'),
        ('CSF', 'Cerebrospinal Fluid'),
    ]

    order_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    patient = models.ForeignKey(PatientRecord, on_delete=models.CASCADE, related_name='lab_orders')
    doctor = models.ForeignKey(PractitionerDoctor, on_delete=models.PROTECT, related_name='lab_orders')
    test_code = models.CharField(max_length=50, default='CBC-01')
    test_name = models.CharField(max_length=200, default='Complete Blood Count (CBC) with Differential')
    sample_type = models.CharField(max_length=20, choices=SAMPLE_TYPES, default='BLOOD')
    specimen_barcode = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDERED')
    result_summary = models.TextField(blank=True, help_text="Pathologist diagnostic impression & findings")
    result_values_json = models.JSONField(default=dict, blank=True, help_text="Key-value test parameter readings (e.g. Hb, WBC, Platelets)")
    reference_range = models.CharField(max_length=150, blank=True, default='Normal parameters')
    is_abnormal = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('45.00'))
    reported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Laboratory Test Order'
        verbose_name_plural = 'Laboratory Test Orders'

    def __str__(self):
        return f"Lab #{self.order_number[:8]} - {self.test_name} ({self.patient.full_name}) [{self.status}]"


class InpatientAdmission(models.Model):
    WARD_TYPES = [
        ('GENERAL', 'General Ward'),
        ('SEMI_PRIVATE', 'Semi-Private Room'),
        ('PRIVATE', 'Deluxe Private Suite'),
        ('ICU', 'Intensive Care Unit (ICU)'),
        ('CCU', 'Coronary Care Unit (CCU)'),
        ('NICU', 'Neonatal ICU'),
    ]

    STATUS_CHOICES = [
        ('ADMITTED', 'Admitted & Occupying Bed'),
        ('DISCHARGED', 'Discharged & Billed'),
        ('TRANSFERRED', 'Transferred to Higher Facility'),
    ]

    admission_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    patient = models.ForeignKey(PatientRecord, on_delete=models.CASCADE, related_name='admissions')
    admitting_doctor = models.ForeignKey(PractitionerDoctor, on_delete=models.PROTECT, related_name='inpatient_admissions')
    ward_type = models.CharField(max_length=20, choices=WARD_TYPES, default='GENERAL')
    room_number = models.CharField(max_length=50, default='Room 204')
    bed_number = models.CharField(max_length=50, default='Bed B')
    daily_bed_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('250.00'))
    admission_date = models.DateTimeField()
    discharge_date = models.DateTimeField(null=True, blank=True)
    admission_reason = models.TextField()
    discharge_summary = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ADMITTED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-admission_date']
        verbose_name = 'Inpatient Admission (IPD)'
        verbose_name_plural = 'Inpatient Admissions (IPD)'

    def __str__(self):
        return f"IPD #{self.admission_number[:8]} - {self.patient.full_name} ({self.ward_type} - {self.room_number})"


class MedicalBillingInvoice(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Settled & Paid in Full'),
        ('INSURANCE_CLAIMED', 'Insurance TPA Claim Submitted'),
        ('WRITTEN_OFF', 'Charity / Written-Off'),
    ]

    bill_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    patient = models.ForeignKey(PatientRecord, on_delete=models.CASCADE, related_name='medical_bills')
    appointment = models.ForeignKey(AppointmentSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')
    admission = models.ForeignKey(InpatientAdmission, on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')

    consultation_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    lab_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pharmacy_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    room_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    procedure_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    insurance_covered_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    patient_co_pay = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Medical Billing Invoice'
        verbose_name_plural = 'Medical Billing Invoices'

    def __str__(self):
        return f"MedBill #{self.bill_number[:8]} - {self.patient.full_name} (${self.grand_total}) [{self.status}]"
