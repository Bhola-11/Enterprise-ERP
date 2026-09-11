from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from accounting.models import JournalEntry, JournalItem, Account
from organizations.models import Branch
from .models import StudentProfile, CourseEnrollment, StudentFeeInvoice, FeeStructure

class GPACalculator:
    GRADE_SCALE = {
        'A+': Decimal('4.00'), 'A': Decimal('4.00'), 'A-': Decimal('3.70'),
        'B+': Decimal('3.30'), 'B': Decimal('3.00'), 'B-': Decimal('2.70'),
        'C+': Decimal('2.30'), 'C': Decimal('2.00'), 'C-': Decimal('1.70'),
        'D+': Decimal('1.30'), 'D': Decimal('1.00'), 'F': Decimal('0.00'),
    }

    @classmethod
    def marks_to_grade_letter(cls, marks_pct):
        if marks_pct >= 93: return 'A', Decimal('4.00')
        if marks_pct >= 90: return 'A-', Decimal('3.70')
        if marks_pct >= 87: return 'B+', Decimal('3.30')
        if marks_pct >= 83: return 'B', Decimal('3.00')
        if marks_pct >= 80: return 'B-', Decimal('2.70')
        if marks_pct >= 77: return 'C+', Decimal('2.30')
        if marks_pct >= 70: return 'C', Decimal('2.00')
        if marks_pct >= 60: return 'D', Decimal('1.00')
        return 'F', Decimal('0.00')

    @classmethod
    def calculate_student_cgpa(cls, student):
        enrollments = CourseEnrollment.objects.filter(
            student=student, grade_point__isnull=False
        ).select_related('course')

        total_points = Decimal('0.00')
        total_credits = 0

        for en in enrollments:
            cr = en.course.credits
            total_points += (en.grade_point * cr)
            total_credits += cr

        if total_credits > 0:
            cgpa = (total_points / total_credits).quantize(Decimal('0.01'))
            student.current_gpa = cgpa
            student.save(update_fields=['current_gpa'])
            return cgpa
        return Decimal('0.00')


class StudentBillingService:
    @classmethod
    @transaction.atomic
    def generate_session_invoice(cls, student, session):
        structures = FeeStructure.objects.filter(program=student.program, session=session)
        total_fee = sum([s.amount for s in structures]) or student.program.tuition_per_semester

        inv_number = f"EDU-{session.name[:4]}-{student.student_id[-4:]}-{timezone.now().strftime('%m%d%H%M')}"
        invoice, created = StudentFeeInvoice.objects.get_or_create(
            student=student,
            session=session,
            defaults={
                'invoice_number': inv_number,
                'total_amount': total_fee,
                'paid_amount': Decimal('0.00'),
                'balance_amount': total_fee,
                'status': 'PENDING',
                'due_date': session.start_date
            }
        )
        return invoice

    @classmethod
    @transaction.atomic
    def record_fee_payment(cls, invoice, amount, payment_method, reference_no, user=None):
        amount = Decimal(str(amount))
        invoice.paid_amount += amount
        invoice.balance_amount = max(Decimal('0.00'), invoice.total_amount - invoice.paid_amount)
        if invoice.balance_amount == Decimal('0.00'):
            invoice.status = 'PAID'
        else:
            invoice.status = 'PARTIAL'

        invoice.payment_method = payment_method
        invoice.transaction_reference = reference_no
        invoice.paid_at = timezone.now()

        # Integrate with general ledger
        ar_account = Account.objects.filter(account_type='ASSET', name__icontains='Receivable').first()
        if not ar_account:
            ar_account = Account.objects.filter(account_type='ASSET').first()
        cash_account = Account.objects.filter(account_type='ASSET', name__icontains='Cash').first()
        if not cash_account:
            cash_account = Account.objects.filter(account_type='ASSET').first()

        if ar_account and cash_account and user:
            entry = JournalEntry.objects.create(
                entry_number=f"JE-EDU-{invoice.invoice_number}",
                date=timezone.now().date(),
                reference=f"Tuition: {invoice.invoice_number}",
                narration=f"Tuition Fee payment received for student {invoice.student.student_id} ({invoice.invoice_number})",
                status='POSTED',
                total_debit=amount,
                total_credit=amount,
                created_by=user
            )
            JournalItem.objects.create(journal_entry=entry, account=cash_account, debit=amount, credit=Decimal('0.00'), description="Tuition Cash collection")
            JournalItem.objects.create(journal_entry=entry, account=ar_account, debit=Decimal('0.00'), credit=amount, description="Student AR Cleared")
            invoice.journal_entry = entry

        invoice.save()
        return invoice
