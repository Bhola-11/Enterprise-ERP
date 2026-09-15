from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Sum, Count, Q

from .models import ShiftTemplate, ShiftRosterAssignment, BiometricPunchLog, AttendanceSummaryPeriod
from .forms import ShiftTemplateForm, ShiftRosterAssignmentForm, BiometricPunchLogForm
from .services import OvertimeCalculationEngine, RosterConflictChecker
from hr.models import Employee, Department


@login_required
def dashboard(request):
    today = timezone.now().date()
    today_rosters = ShiftRosterAssignment.objects.filter(date=today).select_related('employee', 'shift_template', 'employee__department')

    total_scheduled = today_rosters.count()
    recent_punches = BiometricPunchLog.objects.select_related('employee')[:8]

    # Weekly Overtime Aggregates
    week_ago = today - timedelta(days=7)
    ot_agg = AttendanceSummaryPeriod.objects.filter(date__gte=week_ago).aggregate(
        reg=Sum('regular_hours_worked'),
        ot15=Sum('overtime_1_5x_hours'),
        ot20=Sum('overtime_2_0x_hours')
    )
    total_reg = ot_agg['reg'] or 0
    total_ot15 = ot_agg['ot15'] or 0
    total_ot20 = ot_agg['ot20'] or 0

    shifts = ShiftTemplate.objects.filter(is_active=True)

    context = {
        'today': today,
        'today_rosters': today_rosters,
        'total_scheduled': total_scheduled,
        'recent_punches': recent_punches,
        'total_reg': total_reg,
        'total_ot15': total_ot15,
        'total_ot20': total_ot20,
        'shifts': shifts,
        'page_title': 'Workforce Rostering & Biometric Time Gateway'
    }
    return render(request, 'shifts_rostering/dashboard.html', context)


@login_required
def roster_calendar(request):
    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday()) # Monday
    days = [start_date + timedelta(days=i) for i in range(7)]

    dept_id = request.GET.get('department')
    employees = Employee.objects.filter(status='ACTIVE')
    if dept_id:
        employees = employees.filter(department_id=dept_id)

    roster_grid = []
    for emp in employees[:15]:
        emp_assignments = {}
        for d in days:
            assign = ShiftRosterAssignment.objects.filter(employee=emp, date=d).select_related('shift_template').first()
            emp_assignments[d] = assign
        roster_grid.append({'employee': emp, 'assignments': emp_assignments})

    departments = Department.objects.all()

    context = {
        'days': days,
        'roster_grid': roster_grid,
        'departments': departments,
        'selected_dept': dept_id,
        'page_title': 'Weekly Shift Roster Schedule'
    }
    return render(request, 'shifts_rostering/roster_calendar.html', context)


@login_required
def roster_assign(request):
    if request.method == 'POST':
        form = ShiftRosterAssignmentForm(request.POST)
        if form.is_valid():
            emp = form.cleaned_data['employee']
            dt = form.cleaned_data['date']
            shift = form.cleaned_data['shift_template']
            is_valid, msg = RosterConflictChecker.validate_assignment(emp, dt, shift)
            if not is_valid:
                messages.error(request, msg)
            else:
                r = form.save()
                messages.success(request, f"Scheduled {r.employee} for '{r.shift_template.name}' on {r.date}.")
                return redirect('shifts_rostering:roster_calendar')
    else:
        form = ShiftRosterAssignmentForm(initial={'date': timezone.now().date()})

    return render(request, 'shifts_rostering/roster_form.html', {
        'form': form,
        'page_title': 'Schedule Shift Assignment'
    })


@login_required
def shift_list(request):
    shifts = ShiftTemplate.objects.all()
    return render(request, 'shifts_rostering/shift_list.html', {
        'shifts': shifts,
        'page_title': 'Shift Template Catalog'
    })


@login_required
def shift_create(request):
    if request.method == 'POST':
        form = ShiftTemplateForm(request.POST)
        if form.is_valid():
            s = form.save()
            messages.success(request, f"Shift template '{s.name}' created.")
            return redirect('shifts_rostering:shift_list')
    else:
        form = ShiftTemplateForm()

    return render(request, 'shifts_rostering/shift_form.html', {
        'form': form,
        'page_title': 'Create Shift Template'
    })


@login_required
def punch_portal(request):
    if request.method == 'POST':
        form = BiometricPunchLogForm(request.POST)
        if form.is_valid():
            punch = form.save()
            # Process timesheet calculation
            OvertimeCalculationEngine.process_daily_timesheet(punch.employee, punch.punch_time.date())
            messages.success(request, f"Biometric {punch.get_punch_type_display()} recorded for {punch.employee}.")
            return redirect('shifts_rostering:punch_portal')
    else:
        form = BiometricPunchLogForm(initial={'punch_time': timezone.now()})

    punches = BiometricPunchLog.objects.select_related('employee').all()[:15]

    return render(request, 'shifts_rostering/punch_portal.html', {
        'form': form,
        'punches': punches,
        'page_title': 'Biometric Attendance Terminal & Clock'
    })


@login_required
def timesheet_summary(request):
    summaries = AttendanceSummaryPeriod.objects.select_related('employee', 'shift_template').all()[:30]
    return render(request, 'shifts_rostering/timesheet_summary.html', {
        'summaries': summaries,
        'page_title': 'Daily Timesheets & Overtime Ledger'
    })
