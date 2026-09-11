from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import WorkflowDefinition, WorkflowInstance, ApprovalAction
from .engine import WorkflowEngine

@login_required
def workflow_instance_list(request):
    status_filter = request.GET.get('status', 'PENDING')
    instances = WorkflowInstance.objects.select_related('workflow', 'current_stage', 'requester').all()
    if status_filter != 'ALL':
        instances = instances.filter(status=status_filter)

    paginator = Paginator(instances, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'workflows/instance_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
    })

@login_required
def workflow_instance_detail(request, pk):
    instance = get_object_or_404(WorkflowInstance.objects.select_related('workflow', 'current_stage', 'requester'), pk=pk)
    actions = instance.actions.select_related('actor', 'stage').order_by('timestamp')

    if request.method == 'POST':
        action_type = request.POST.get('action') # APPROVE or REJECT
        comments = request.POST.get('comments', '')
        success, msg = WorkflowEngine.process_action(instance, request.user, action_type, comments, request=request)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
        return redirect('workflows:instance_detail', pk=pk)

    return render(request, 'workflows/instance_detail.html', {
        'instance': instance,
        'actions': actions,
    })

@login_required
def workflow_definitions_list(request):
    definitions = WorkflowDefinition.objects.prefetch_related('stages').all()
    return render(request, 'workflows/definitions_list.html', {'definitions': definitions})
