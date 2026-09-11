from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg
from .models import Project, Task, Timesheet, Milestone
from .forms import ProjectForm, TaskForm, TimesheetForm
from audit.middleware import log_audit_event

@login_required
def project_dashboard(request):
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status='ACTIVE').count()
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='DONE').count()
    total_budget = Project.objects.aggregate(Sum('budget'))['budget__sum'] or 0

    recent_projects = Project.objects.select_related('project_manager', 'client').order_by('-start_date')[:6]
    my_tasks = Task.objects.filter(assigned_to=request.user, status__in=['TODO', 'IN_PROGRESS', 'IN_REVIEW'])[:8]

    return render(request, 'projects/dashboard.html', {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'total_budget': total_budget,
        'recent_projects': recent_projects,
        'my_tasks': my_tasks,
    })

@login_required
def project_list(request):
    projects = Project.objects.select_related('project_manager', 'client').all()
    status_filter = request.GET.get('status')
    if status_filter:
        projects = projects.filter(status=status_filter)

    paginator = Paginator(projects, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'projects/project_list.html', {'page_obj': page_obj, 'statuses': Project.STATUS_CHOICES, 'selected_status': status_filter})

@login_required
def project_create(request):
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        proj = form.save()
        log_audit_event(request.user, 'CREATE', 'Project', proj.id, str(proj), request=request)
        messages.success(request, f"Project '{proj.name}' created successfully!")
        return redirect('projects:project_list')
    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Create New Project'})

@login_required
def project_detail(request, pk):
    proj = get_object_or_404(Project.objects.select_related('project_manager', 'client'), pk=pk)
    tasks = proj.tasks.select_related('assigned_to', 'milestone').all()
    milestones = proj.milestones.all()
    
    # Kanban task grouping
    todo_tasks = tasks.filter(status='TODO')
    in_progress_tasks = tasks.filter(status='IN_PROGRESS')
    review_tasks = tasks.filter(status='IN_REVIEW')
    done_tasks = tasks.filter(status='DONE')

    task_form = TaskForm(request.POST or None, initial={'project': proj})
    if request.method == 'POST' and 'add_task' in request.POST:
        if task_form.is_valid():
            tsk = task_form.save(commit=False)
            tsk.project = proj
            tsk.save()
            log_audit_event(request.user, 'CREATE', 'Task', tsk.id, str(tsk), request=request)
            messages.success(request, f"Task '{tsk.title}' added to project.")
            return redirect('projects:project_detail', pk=pk)

    return render(request, 'projects/project_detail.html', {
        'project': proj,
        'tasks': tasks,
        'milestones': milestones,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'review_tasks': review_tasks,
        'done_tasks': done_tasks,
        'task_form': task_form,
    })

@login_required
def task_status_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    new_status = request.POST.get('status')
    if new_status in ['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE']:
        task.status = new_status
        task.save(update_fields=['status'])
        log_audit_event(request.user, 'UPDATE', 'Task', task.id, str(task), request=request, description=f"Updated task status to {new_status}")
    return redirect('projects:project_detail', pk=task.project.id)

@login_required
def timesheet_list(request):
    timesheets = Timesheet.objects.select_related('employee', 'task__project').all()
    paginator = Paginator(timesheets, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'projects/timesheet_list.html', {'page_obj': page_obj})
