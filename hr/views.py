from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Employee, Designation, Attendance, LeaveRequest, Holiday, LeaveType
from .forms import EmployeeForm, LeaveRequestForm, AttendanceForm
from organizations.models import Department, Branch
from audit.middleware import log_audit_event
from workflows.engine import WorkflowEngine

@login_required
def hr_dashboard(request):
    total_employees = Employee.objects.filter(status='ACTIVE').count()
    dept_count = Department.objects.filter(is_active=True).count()
    pending_leaves = LeaveRequest.objects.filter(status='PENDING').count()
    today = timezone.now().date()
    today_present = Attendance.objects.filter(date=today, status='PRESENT').count()

    recent_employees = Employee.objects.select_related('department', 'designation').order_by('-joining_date')[:6]
    upcoming_holidays = Holiday.objects.filter(date__gte=today)[:5]

    return render(request, 'hr/dashboard.html', {
        'total_employees': total_employees,
        'dept_count': dept_count,
        'pending_leaves': pending_leaves,
        'today_present': today_present,
        'recent_employees': recent_employees,
        'upcoming_holidays': upcoming_holidays,
    })

@login_required
def employee_list(request):
    employees = Employee.objects.select_related('department', 'designation', 'branch', 'manager').all()
    dept_id = request.GET.get('dept')
    search = request.GET.get('q')

    if dept_id:
        employees = employees.filter(department_id=dept_id)
    if search:
        employees = employees.filter(models.Q(first_name__icontains=search) | models.Q(last_name__icontains=search) | models.Q(employee_id__icontains=search) | models.Q(email__icontains=search))

    paginator = Paginator(employees, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    departments = Department.objects.filter(is_active=True)

    return render(request, 'hr/employee_list.html', {
        'page_obj': page_obj,
        'departments': departments,
        'selected_dept': dept_id,
        'search_query': search,
    })

@login_required
def employee_create(request):
    form = EmployeeForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        emp = form.save()
        log_audit_event(request.user, 'CREATE', 'Employee', emp.id, str(emp), request=request)
        messages.success(request, f'Employee {emp.full_name} ({emp.employee_id}) onboarded successfully!')
        return redirect('hr:employee_list')
    return render(request, 'hr/employee_form.html', {'form': form, 'title': 'Onboard New Employee'})

@login_required
def employee_detail(request, pk):
    emp = get_object_or_404(Employee.objects.select_related('department', 'designation', 'branch', 'manager'), pk=pk)
    attendances = emp.attendances.all()[:10]
    leaves = emp.leave_requests.select_related('leave_type')[:5]
    return render(request, 'hr/employee_detail.html', {'emp': emp, 'attendances': attendances, 'leaves': leaves})

@login_required
def org_chart_view(request):
    departments = Department.objects.prefetch_related('employees__designation').all()
    return render(request, 'hr/org_chart.html', {'departments': departments})

@login_required
def leave_list(request):
    leaves = LeaveRequest.objects.select_related('employee', 'leave_type').all()
    status_filter = request.GET.get('status')
    if status_filter:
        leaves = leaves.filter(status=status_filter)

    paginator = Paginator(leaves, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'hr/leave_list.html', {'page_obj': page_obj, 'status_filter': status_filter})

@login_required
def leave_request_create(request):
    # Try to find current user's employee record
    emp = getattr(request.user, 'employee_profile', None)
    form = LeaveRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        lr = form.save(commit=False)
        if emp:
            lr.employee = emp
        else:
            first_emp = Employee.objects.first()
            lr.employee = first_emp
        lr.save()
        WorkflowEngine.start_workflow('LEAVE', lr, request.user, amount=0.0, notes=f"Leave request: {lr.total_days} days")
        messages.success(request, 'Leave request submitted successfully for approval!')
        return redirect('hr:leave_list')
    return render(request, 'hr/leave_form.html', {'form': form})

@login_required
def attendance_list(request):
    attendances = Attendance.objects.select_related('employee__department').all()
    date_val = request.GET.get('date')
    if date_val:
        attendances = attendances.filter(date=date_val)

    paginator = Paginator(attendances, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'hr/attendance_list.html', {'page_obj': page_obj, 'selected_date': date_val})
