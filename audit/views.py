from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import AuditLog

@login_required
def audit_log_list(request):
    logs = AuditLog.objects.select_related('user').all()
    action = request.GET.get('action')
    model = request.GET.get('model')
    search = request.GET.get('q')

    if action:
        logs = logs.filter(action=action)
    if model:
        logs = logs.filter(model_name__icontains=model)
    if search:
        logs = logs.filter(object_repr__icontains=search)

    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    actions = AuditLog.ACTION_CHOICES
    return render(request, 'audit/log_list.html', {
        'page_obj': page_obj,
        'actions': actions,
        'selected_action': action,
        'selected_model': model,
        'search_query': search,
    })
