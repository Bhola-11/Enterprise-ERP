from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q

from .models import CriticalRolePosition, TalentProfile, SuccessionPlan
from .forms import CriticalRolePositionForm, TalentProfileForm, SuccessionPlanForm
from .services import NineBoxMatrixService, BenchStrengthService
from hr.models import Employee, Department


@login_required
def dashboard(request):
    kpis = BenchStrengthService.get_enterprise_pipeline_kpis()
    critical_roles = CriticalRolePosition.objects.select_related('department', 'current_incumbent').filter(is_active=True)[:6]
    ready_now_successors = SuccessionPlan.objects.select_related('critical_position', 'successor_employee').filter(readiness_level='READY_NOW', status='ACTIVE')[:6]
    high_flight_risks = TalentProfile.objects.select_related('employee', 'employee__department').filter(flight_risk='HIGH')[:5]

    context = {
        'kpis': kpis,
        'critical_roles': critical_roles,
        'ready_now_successors': ready_now_successors,
        'high_flight_risks': high_flight_risks,
        'page_title': 'Enterprise Succession & Leadership Pipeline'
    }
    return render(request, 'succession_planning/dashboard.html', context)


@login_required
def nine_box_matrix(request):
    dept_id = request.GET.get('department')
    matrix = NineBoxMatrixService.get_full_matrix_grid()
    departments = Department.objects.all()

    total_calibrated = TalentProfile.objects.count()

    context = {
        'matrix': matrix,
        'departments': departments,
        'selected_dept': dept_id,
        'total_calibrated': total_calibrated,
        'page_title': '9-Box Talent Calibration Matrix'
    }
    return render(request, 'succession_planning/nine_box_matrix.html', context)


@login_required
def role_list(request):
    search_q = request.GET.get('q', '')
    dept_id = request.GET.get('department', '')

    roles = CriticalRolePosition.objects.select_related('department', 'current_incumbent').all()
    if search_q:
        roles = roles.filter(Q(title__icontains=search_q) | Q(position_code__icontains=search_q))
    if dept_id:
        roles = roles.filter(department_id=dept_id)

    departments = Department.objects.all()

    context = {
        'roles': roles,
        'departments': departments,
        'search_q': search_q,
        'selected_dept': dept_id,
        'page_title': 'Critical Key Roles & Leadership Positions'
    }
    return render(request, 'succession_planning/role_list.html', context)


@login_required
def role_create(request):
    if request.method == 'POST':
        form = CriticalRolePositionForm(request.POST)
        if form.is_valid():
            role = form.save()
            messages.success(request, f"Critical position '{role.title}' registered successfully.")
            return redirect('succession_planning:role_detail', pk=role.id)
    else:
        form = CriticalRolePositionForm()

    return render(request, 'succession_planning/role_form.html', {
        'form': form,
        'page_title': 'Register Critical Leadership Role'
    })


@login_required
def role_detail(request, pk):
    role = get_object_or_404(CriticalRolePosition, pk=pk)
    successors = role.succession_candidates.select_related('successor_employee', 'successor_employee__department').all()

    if request.method == 'POST':
        form = SuccessionPlanForm(request.POST)
        if form.is_valid():
            nom = form.save(commit=False)
            nom.critical_position = role
            nom.save()
            messages.success(request, f"Nominated {nom.successor_employee} as successor.")
            return redirect('succession_planning:role_detail', pk=role.id)
    else:
        form = SuccessionPlanForm(initial={'critical_position': role})

    context = {
        'role': role,
        'successors': successors,
        'form': form,
        'page_title': f"Role Succession Plan: {role.title}"
    }
    return render(request, 'succession_planning/role_detail.html', context)


@login_required
def talent_list(request):
    flight_filter = request.GET.get('flight_risk', '')
    pot_filter = request.GET.get('potential', '')

    profiles = TalentProfile.objects.select_related('employee', 'employee__department', 'employee__designation').all()
    if flight_filter:
        profiles = profiles.filter(flight_risk=flight_filter)
    if pot_filter:
        profiles = profiles.filter(potential_rating=pot_filter)

    context = {
        'profiles': profiles,
        'flight_filter': flight_filter,
        'pot_filter': pot_filter,
        'page_title': 'Talent Profiles & 9-Box Calibration Register'
    }
    return render(request, 'succession_planning/talent_list.html', context)


@login_required
def talent_edit(request, employee_id=None):
    profile = None
    if employee_id:
        emp = get_object_or_404(Employee, pk=employee_id)
        profile, _ = TalentProfile.objects.get_or_create(employee=emp)

    if request.method == 'POST':
        form = TalentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            p = form.save()
            messages.success(request, f"Talent Profile for {p.employee} calibrated: {p.get_nine_box_quadrant_display()}.")
            return redirect('succession_planning:talent_list')
    else:
        form = TalentProfileForm(instance=profile)

    return render(request, 'succession_planning/talent_form.html', {
        'form': form,
        'profile': profile,
        'page_title': f"Calibrate Talent Profile"
    })
