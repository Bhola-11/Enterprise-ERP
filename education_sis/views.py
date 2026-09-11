from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q

from .models import (
    DepartmentFaculty, AcademicProgram, AcademicSession, StudentProfile,
    CourseModule, CourseEnrollment, StudentFeeInvoice, ExamSchedule, StudentGradeResult
)
from .forms import StudentProfileForm, CourseModuleForm, CourseEnrollmentForm, FeePaymentForm
from .services import GPACalculator, StudentBillingService


@login_required
def sis_dashboard(request):
    total_students = StudentProfile.objects.filter(academic_status='ENROLLED').count()
    total_programs = AcademicProgram.objects.count()
    active_session = AcademicSession.objects.filter(is_active=True).first()
    
    total_fees_due = StudentFeeInvoice.objects.filter(status__in=['PENDING', 'PARTIAL', 'OVERDUE']).aggregate(s=Sum('balance_amount'))['s'] or Decimal('0.00')
    total_fees_collected = StudentFeeInvoice.objects.aggregate(s=Sum('paid_amount'))['s'] or Decimal('0.00')

    recent_students = StudentProfile.objects.select_related('program').order_by('-created_at')[:8]
    courses_count = CourseModule.objects.count()

    context = {
        'total_students': total_students,
        'total_programs': total_programs,
        'active_session': active_session,
        'total_fees_due': total_fees_due,
        'total_fees_collected': total_fees_collected,
        'recent_students': recent_students,
        'courses_count': courses_count,
        'page_title': 'Education SIS & Campus ERP Hub',
    }
    return render(request, 'education_sis/dashboard.html', context)


@login_required
def student_list(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    program_id = request.GET.get('program', '')

    students = StudentProfile.objects.select_related('program', 'program__department').order_by('-admission_date')

    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    if status:
        students = students.filter(academic_status=status)
    if program_id:
        students = students.filter(program_id=program_id)

    programs = AcademicProgram.objects.all()

    return render(request, 'education_sis/student_list.html', {
        'students': students[:100],
        'programs': programs,
        'query': query,
        'selected_status': status,
        'selected_program': program_id,
        'page_title': 'Student Directory & Records'
    })


@login_required
def student_create(request):
    if request.method == 'POST':
        form = StudentProfileForm(request.POST)
        if form.is_valid():
            student = form.save()
            # Generate initial fee invoice for active session
            active_session = AcademicSession.objects.filter(is_active=True).first()
            if active_session:
                StudentBillingService.generate_session_invoice(student, active_session)

            messages.success(request, f"Student {student.full_name} ({student.student_id}) enrolled successfully.")
            return redirect('education_sis:student_profile', pk=student.id)
    else:
        # Generate initial student ID
        next_id = f"STU-{timezone.now().year}-{StudentProfile.objects.count() + 1:04d}"
        form = StudentProfileForm(initial={'student_id': next_id, 'admission_date': timezone.now().date()})

    return render(request, 'education_sis/student_form.html', {'form': form, 'page_title': 'New Student Admission & Enrollment'})


@login_required
def student_profile(request, pk):
    student = get_object_or_404(StudentProfile.objects.select_related('program', 'program__department'), pk=pk)
    enrollments = student.enrollments.select_related('course', 'session').order_by('-session__start_date')
    invoices = student.fee_invoices.select_related('session').order_by('-created_at')
    exam_results = student.exam_results.select_related('exam', 'exam__course', 'exam__session').order_by('-exam__exam_date')

    # Recompute CGPA
    cgpa = GPACalculator.calculate_student_cgpa(student)

    return render(request, 'education_sis/student_profile.html', {
        'student': student,
        'enrollments': enrollments,
        'invoices': invoices,
        'exam_results': exam_results,
        'cgpa': cgpa,
        'page_title': f'Student Transcript & Profile: {student.full_name}'
    })


@login_required
def course_list(request):
    courses = CourseModule.objects.select_related('program', 'program__department').order_by('program', 'semester_recommended')
    return render(request, 'education_sis/course_list.html', {
        'courses': courses,
        'page_title': 'Academic Course Catalog & Modules'
    })


@login_required
def fee_invoice_list(request):
    invoices = StudentFeeInvoice.objects.select_related('student', 'session').order_by('-created_at')
    return render(request, 'education_sis/fee_invoice_list.html', {
        'invoices': invoices[:100],
        'page_title': 'Student Fee Invoicing & Ledger'
    })


@login_required
def fee_payment_process(request, pk):
    invoice = get_object_or_404(StudentFeeInvoice, pk=pk)
    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['payment_amount']
            method = form.cleaned_data['payment_method']
            ref = form.cleaned_data['reference_number']
            StudentBillingService.record_fee_payment(invoice, amount, method, ref, user=request.user)
            messages.success(request, f"Payment of ${amount} applied to Invoice #{invoice.invoice_number}.")
            return redirect('education_sis:fee_invoice_list')
    else:
        form = FeePaymentForm(initial={'payment_amount': invoice.balance_amount})

    return render(request, 'education_sis/fee_payment_modal.html', {'invoice': invoice, 'form': form, 'page_title': f'Process Fee Payment: {invoice.invoice_number}'})


@login_required
def grade_book(request):
    enrollments = CourseEnrollment.objects.select_related('student', 'course', 'session').order_by('session', 'course')
    return render(request, 'education_sis/grade_book.html', {
        'enrollments': enrollments[:150],
        'page_title': 'Master Academic Grade Book & Transcripts'
    })
