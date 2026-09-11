from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import SupportTicket, TicketComment, TicketCategory
from .forms import TicketForm, CommentForm
from audit.middleware import log_audit_event
from notifications.models import notify_user

@login_required
def support_dashboard(request):
    open_tickets = SupportTicket.objects.filter(status='OPEN').count()
    in_prog_tickets = SupportTicket.objects.filter(status='IN_PROGRESS').count()
    resolved_tickets = SupportTicket.objects.filter(status='RESOLVED').count()
    urgent_tickets = SupportTicket.objects.filter(priority='URGENT', status__in=['OPEN', 'IN_PROGRESS']).count()

    recent_tickets = SupportTicket.objects.select_related('customer', 'category', 'assigned_to').order_by('-created_at')[:6]

    return render(request, 'support/dashboard.html', {
        'open_tickets': open_tickets,
        'in_prog_tickets': in_prog_tickets,
        'resolved_tickets': resolved_tickets,
        'urgent_tickets': urgent_tickets,
        'recent_tickets': recent_tickets,
    })

@login_required
def ticket_list(request):
    tickets = SupportTicket.objects.select_related('customer', 'category', 'assigned_to').all()
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    search = request.GET.get('q')

    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if search:
        tickets = tickets.filter(models.Q(subject__icontains=search) | models.Q(ticket_id__icontains=search) | models.Q(customer__first_name__icontains=search))

    paginator = Paginator(tickets, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'support/ticket_list.html', {
        'page_obj': page_obj,
        'statuses': SupportTicket.STATUS_CHOICES,
        'priorities': SupportTicket.PRIORITY_CHOICES,
        'selected_status': status_filter,
        'selected_priority': priority_filter,
    })

@login_required
def ticket_create(request):
    form = TicketForm(request.POST or None, initial={'ticket_id': f"TIK-2026-{SupportTicket.objects.count() + 1:04d}"})
    if request.method == 'POST' and form.is_valid():
        ticket = form.save()
        log_audit_event(request.user, 'CREATE', 'SupportTicket', ticket.id, str(ticket), request=request)
        if ticket.assigned_to:
            notify_user(
                recipient=ticket.assigned_to,
                title=f"Support Ticket Assigned: {ticket.ticket_id}",
                message=f"You have been assigned ticket '{ticket.subject}' for {ticket.customer}.",
                category='SUPPORT',
                priority='HIGH',
                link=f"/support/tickets/{ticket.id}/"
            )
        messages.success(request, f"Support Ticket #{ticket.ticket_id} created successfully!")
        return redirect('support:ticket_list')
    return render(request, 'support/ticket_form.html', {'form': form, 'title': 'Create Support Ticket'})

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(SupportTicket.objects.select_related('customer', 'category', 'assigned_to'), pk=pk)
    comments = ticket.comments.select_related('author').all()
    comment_form = CommentForm(request.POST or None)

    if request.method == 'POST':
        if 'add_comment' in request.POST and comment_form.is_valid():
            com = comment_form.save(commit=False)
            com.ticket = ticket
            com.author = request.user
            com.save()
            log_audit_event(request.user, 'CREATE', 'TicketComment', com.id, str(com), request=request)
            messages.success(request, 'Reply submitted!')
            return redirect('support:ticket_detail', pk=pk)

        elif 'update_status' in request.POST:
            new_status = request.POST.get('status')
            ticket.status = new_status
            if new_status in ['RESOLVED', 'CLOSED']:
                ticket.resolved_at = timezone.now()
            ticket.save(update_fields=['status', 'resolved_at'])
            log_audit_event(request.user, 'UPDATE', 'SupportTicket', ticket.id, str(ticket), request=request, description=f"Updated status to {new_status}")
            messages.success(request, f"Ticket status updated to {ticket.get_status_display()}.")
            return redirect('support:ticket_detail', pk=pk)

    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'comments': comments,
        'comment_form': comment_form,
        'statuses': SupportTicket.STATUS_CHOICES,
    })
