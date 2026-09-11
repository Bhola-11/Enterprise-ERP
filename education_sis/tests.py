from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from organizations.models import Organization, Branch
from accounting.models import Account
from education_sis.models import (
    DepartmentFaculty, AcademicProgram, AcademicSession, StudentProfile,
    CourseModule, CourseEnrollment, StudentFeeInvoice
)
from education_sis.services import GPACalculator, StudentBillingService

User = get_user_model()

class EducationSISTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='sis_admin', email='sis@nexora.io', password='Password123!', role='ADMIN')
        self.org = Organization.objects.create(name='Global University')
        self.branch = Branch.objects.create(organization=self.org, name='Main Campus', code='UNI-01')
        self.cash_acc = Account.objects.create(
            code='1010', name='Cash on Hand', account_type='ASSET', is_active=True
        )
        self.ar_acc = Account.objects.create(
            code='1120', name='Accounts Receivable Tuition', account_type='ASSET', is_active=True
        )

        self.dept = DepartmentFaculty.objects.create(name='School of Computing', code='CS')
        self.prog = AcademicProgram.objects.create(
            department=self.dept, name='B.S. Computer Science', code='BSCS',
            degree_level='BACHELOR', duration_semesters=8, total_credits_required=120,
            tuition_per_semester=Decimal('5000.00')
        )
        self.session = AcademicSession.objects.create(
            name='2026-Fall', term='FALL', start_date='2026-09-01', end_date='2026-12-20', is_active=True
        )
        self.student = StudentProfile.objects.create(
            student_id='STU-2026-0001', first_name='Alexander', last_name='Wright',
            email='alex.wright@campus.edu', phone='+1-555-0987', date_of_birth='2004-05-15',
            gender='MALE', program=self.prog, current_semester=1, academic_status='ENROLLED'
        )
        self.course1 = CourseModule.objects.create(
            program=self.prog, code='CS101', title='Intro to Algorithms', credits=4
        )
        self.course2 = CourseModule.objects.create(
            program=self.prog, code='MATH201', title='Discrete Mathematics', credits=3
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_gpa_calculation(self):
        CourseEnrollment.objects.create(
            student=self.student, course=self.course1, session=self.session,
            final_grade_letter='A', grade_point=Decimal('4.00'), status='PASSED'
        )
        CourseEnrollment.objects.create(
            student=self.student, course=self.course2, session=self.session,
            final_grade_letter='B', grade_point=Decimal('3.00'), status='PASSED'
        )
        cgpa = GPACalculator.calculate_student_cgpa(self.student)
        self.assertEqual(cgpa, Decimal('3.57'))

    def test_fee_billing_and_payment(self):
        invoice = StudentBillingService.generate_session_invoice(self.student, self.session)
        self.assertEqual(invoice.total_amount, Decimal('5000.00'))
        self.assertEqual(invoice.balance_amount, Decimal('5000.00'))

        StudentBillingService.record_fee_payment(
            invoice=invoice, amount=Decimal('5000.00'),
            payment_method='ONLINE', reference_no='TXN-TEST-1234', user=self.user
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'PAID')
        self.assertEqual(invoice.balance_amount, Decimal('0.00'))
        self.assertIsNotNone(invoice.journal_entry)

    def test_views(self):
        res = self.client.get(reverse('education_sis:dashboard'))
        self.assertEqual(res.status_code, 200)

        res_students = self.client.get(reverse('education_sis:student_list'))
        self.assertEqual(res_students.status_code, 200)
