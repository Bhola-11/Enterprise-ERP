import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from accounting.models import JournalEntry

class DepartmentFaculty(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    dean_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    building_location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name_plural = "Department Faculties"


class AcademicProgram(models.Model):
    DEGREE_CHOICES = [
        ('BACHELOR', 'Bachelor of Science / Arts'),
        ('MASTER', 'Master of Science / MBA'),
        ('DOCTORAL', 'Doctor of Philosophy (PhD)'),
        ('DIPLOMA', 'Postgraduate Diploma'),
        ('CERTIFICATE', 'Executive Certificate'),
    ]
    department = models.ForeignKey(DepartmentFaculty, on_delete=models.CASCADE, related_name='programs')
    name = models.CharField(max_length=250)
    code = models.CharField(max_length=30, unique=True)
    degree_level = models.CharField(max_length=20, choices=DEGREE_CHOICES, default='BACHELOR')
    duration_semesters = models.PositiveIntegerField(default=8)
    total_credits_required = models.PositiveIntegerField(default=120)
    tuition_per_semester = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('4500.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.get_degree_level_display()})"


class AcademicSession(models.Model):
    TERM_CHOICES = [
        ('FALL', 'Fall Semester'),
        ('SPRING', 'Spring Semester'),
        ('SUMMER', 'Summer Term'),
        ('WINTER', 'Winter Intersession'),
    ]
    name = models.CharField(max_length=100) # e.g. 2026-2027 Fall
    term = models.CharField(max_length=20, choices=TERM_CHOICES, default='FALL')
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_term_display()})"


class StudentProfile(models.Model):
    STATUS_CHOICES = [
        ('ENROLLED', 'Active Enrolled'),
        ('PROBATION', 'Academic Probation'),
        ('SUSPENDED', 'Suspended'),
        ('GRADUATED', 'Graduated / Alumni'),
        ('WITHDRAWN', 'Withdrawn'),
    ]
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ]
    student_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='MALE')
    program = models.ForeignKey(AcademicProgram, on_delete=models.PROTECT, related_name='students')
    current_semester = models.PositiveIntegerField(default=1)
    admission_date = models.DateField(default=timezone.now)
    academic_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ENROLLED')
    current_gpa = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"


class CourseModule(models.Model):
    program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, related_name='courses')
    code = models.CharField(max_length=30)
    title = models.CharField(max_length=250)
    credits = models.PositiveIntegerField(default=3)
    semester_recommended = models.PositiveIntegerField(default=1)
    syllabus_summary = models.TextField(blank=True)
    is_elective = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code}: {self.title} ({self.credits} cr)"


class CourseEnrollment(models.Model):
    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('ATTENDING', 'Attending'),
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
        ('DROPPED', 'Dropped'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='enrollments')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    final_grade_letter = models.CharField(max_length=5, blank=True) # A, A-, B+, etc.
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATTENDING')

    class Meta:
        unique_together = ('student', 'course', 'session')

    def __str__(self):
        return f"{self.student.student_id} - {self.course.code} ({self.session.name})"


class FeeStructure(models.Model):
    FEE_TYPES = [
        ('TUITION', 'Semester Tuition Fee'),
        ('LAB', 'Laboratory & Computer Facilities'),
        ('LIBRARY', 'Library & Digital Resources'),
        ('EXAMINATION', 'Semester Examination Fee'),
        ('HOSTEL', 'Campus Housing / Residence'),
        ('ACTIVITY', 'Student Activities & Sports'),
    ]
    program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, related_name='fee_structures')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='fee_structures')
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES, default='TUITION')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"{self.program.code} - {self.get_fee_type_display()}: ${self.amount}"


class StudentFeeInvoice(models.Model):
    PAYMENT_STATUS = [
        ('PENDING', 'Pending Payment'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Paid in Full'),
        ('OVERDUE', 'Overdue'),
        ('WAIVED', 'Scholarship / Waived'),
    ]
    invoice_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='fee_invoices')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='fee_invoices')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    due_date = models.DateField()
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"INV-{self.invoice_number} - {self.student.full_name} (${self.total_amount})"


class ExamSchedule(models.Model):
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='exams')
    course = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='exams')
    exam_title = models.CharField(max_length=200) # Midterm Examination, Final Exam
    exam_date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=120)
    room_hall = models.CharField(max_length=100, default='Main Examination Hall')
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('100.00'))

    def __str__(self):
        return f"{self.course.code} - {self.exam_title} ({self.exam_date})"


class StudentGradeResult(models.Model):
    exam = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='exam_results')
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    grade_letter = models.CharField(max_length=5, blank=True)
    feedback_remarks = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    graded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('exam', 'student')

    def __str__(self):
        return f"{self.student.student_id} - {self.exam.course.code}: {self.marks_obtained}/{self.exam.max_marks}"
