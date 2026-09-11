from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Organization, Branch, Department, CostCenter, FiscalYear, TaxSetting
from .forms import OrganizationForm, BranchForm, DepartmentForm
from audit.middleware import log_audit_event

@login_required
def organization_settings(request):
    org = Organization.objects.first()
    if not org:
        org = Organization.objects.create()

    form = OrganizationForm(request.POST or None, request.FILES or None, instance=org)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_audit_event(request.user, 'UPDATE', 'Organization', org.id, str(org), request=request, description='Updated company profile')
        messages.success(request, 'Organization settings updated successfully!')
        return redirect('organizations:settings')

    branches = Branch.objects.filter(organization=org)
    departments = Department.objects.filter(organization=org)
    cost_centers = CostCenter.objects.filter(organization=org)
    fiscal_years = FiscalYear.objects.filter(organization=org)
    taxes = TaxSetting.objects.filter(organization=org)

    return render(request, 'organizations/settings.html', {
        'form': form,
        'org': org,
        'branches': branches,
        'departments': departments,
        'cost_centers': cost_centers,
        'fiscal_years': fiscal_years,
        'taxes': taxes,
    })

@login_required
def branch_create_or_edit(request, branch_id=None):
    branch = get_object_or_404(Branch, id=branch_id) if branch_id else None
    form = BranchForm(request.POST or None, instance=branch)
    if request.method == 'POST' and form.is_valid():
        b = form.save()
        action = 'UPDATE' if branch else 'CREATE'
        log_audit_event(request.user, action, 'Branch', b.id, str(b), request=request)
        messages.success(request, f'Branch {b.name} saved successfully!')
        return redirect('organizations:settings')
    return render(request, 'organizations/branch_form.html', {'form': form, 'branch': branch})

@login_required
def department_create_or_edit(request, dept_id=None):
    dept = get_object_or_404(Department, id=dept_id) if dept_id else None
    form = DepartmentForm(request.POST or None, instance=dept)
    if request.method == 'POST' and form.is_valid():
        d = form.save()
        action = 'UPDATE' if dept else 'CREATE'
        log_audit_event(request.user, action, 'Department', d.id, str(d), request=request)
        messages.success(request, f'Department {d.name} saved successfully!')
        return redirect('organizations:settings')
    return render(request, 'organizations/department_form.html', {'form': form, 'dept': dept})
