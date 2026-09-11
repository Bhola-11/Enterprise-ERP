from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Notification

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    unread_only = request.GET.get('unread')
    if unread_only:
        notifications = notifications.filter(is_read=False)

    paginator = Paginator(notifications, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'notifications/list.html', {'page_obj': page_obj})

@login_required
def mark_as_read(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications:list')

@login_required
def mark_all_as_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect('notifications:list')
