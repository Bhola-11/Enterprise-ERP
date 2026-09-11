from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q

from .models import (
    InspectionPlan, InspectionCharacteristic, QualityInspectionTicket,
    InspectionResultMetric, NonConformanceReport, CAPAAction
)
from .forms import (
    InspectionPlanForm, InspectionTicketCreateForm, InspectionVerdictForm,
    NonConformanceReportForm, CAPAActionForm
)
from .services import SamplingEngine, QualityDispositionService


@login_required
def qc_dashboard(request):
    total_inspections = QualityInspectionTicket.objects.count()
    pending_inspections = QualityInspectionTicket.objects.filter(status='PENDING').count()
    rejected_lots = QualityInspectionTicket.objects.filter(disposition='REJECTED').count()
    open_ncrs = NonConformanceReport.objects.filter(status__in=['OPEN', 'UNDER_INVESTIGATION', 'CAPA_INITIATED']).count()

    recent_tickets = QualityInspectionTicket.objects.select_related('plan', 'inspector').order_by('-created_at')[:8]
    active_ncrs = NonConformanceReport.objects.select_related('ticket', 'reported_by').order_by('-created_at')[:6]

    context = {
        'total_inspections': total_inspections,
        'pending_inspections': pending_inspections,
        'rejected_lots': rejected_lots,
        'open_ncrs': open_ncrs,
        'recent_tickets': recent_tickets,
        'active_ncrs': active_ncrs,
        'page_title': 'Enterprise Quality Control & Assurance (QC/QA) Hub',
    }
    return render(request, 'quality_control/dashboard.html', context)


@login_required
def plan_list(request):
    plans = InspectionPlan.objects.annotate(chars_count=Count('characteristics')).all()
    return render(request, 'quality_control/plan_list.html', {
        'plans': plans,
        'page_title': 'Quality Inspection Plans & Characteristics'
    })


@login_required
def plan_create(request):
    if request.method == 'POST':
        form = InspectionPlanForm(request.POST)
        if form.is_valid():
            p = form.save()
            messages.success(request, f"Inspection Plan {p.code} created.")
            return redirect('quality_control:plan_list')
    else:
        form = InspectionPlanForm()
    return render(request, 'quality_control/plan_form.html', {'form': form, 'page_title': 'Create Inspection Plan'})


@login_required
def ticket_list(request):
    status = request.GET.get('status', '')
    disposition = request.GET.get('disposition', '')

    tickets = QualityInspectionTicket.objects.select_related('plan', 'inspector').order_by('-created_at')
    if status:
        tickets = tickets.filter(status=status)
    if disposition:
        tickets = tickets.filter(disposition=disposition)

    return render(request, 'quality_control/ticket_list.html', {
        'tickets': tickets[:100],
        'selected_status': status,
        'selected_disposition': disposition,
        'page_title': 'Quality Inspection Gate Tickets'
    })


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = InspectionTicketCreateForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.ticket_number = f"QC-{timezone.now().strftime('%y%m%d%H%M')}"
            ticket.sample_size = SamplingEngine.compute_sample_size(ticket.lot_size, ticket.plan.sampling_standard)
            ticket.status = 'PENDING'
            ticket.save()
            messages.success(request, f"Inspection Ticket #{ticket.ticket_number} created (Sample Size: {ticket.sample_size}).")
            return redirect('quality_control:ticket_detail', pk=ticket.id)
    else:
        form = InspectionTicketCreateForm(initial={
            'lot_size': 100,
            'inspection_date': timezone.now().date(),
        })

    return render(request, 'quality_control/ticket_form.html', {'form': form, 'page_title': 'Generate Quality Inspection Gate'})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(QualityInspectionTicket.objects.select_related('plan', 'inspector'), pk=pk)
    ncrs = ticket.ncrs.all()

    if request.method == 'POST':
        verdict_form = InspectionVerdictForm(request.POST)
        if verdict_form.is_valid():
            acc = verdict_form.cleaned_data['accepted_quantity']
            rej = verdict_form.cleaned_data['rejected_quantity']
            notes = verdict_form.cleaned_data['inspector_notes']
            QualityDispositionService.record_inspection_verdict(ticket, acc, rej, notes, user=request.user)
            messages.success(request, f"Inspection verdict recorded: {ticket.get_disposition_display()}")
            return redirect('quality_control:ticket_detail', pk=ticket.id)
    else:
        verdict_form = InspectionVerdictForm(initial={
            'accepted_quantity': ticket.sample_size,
            'rejected_quantity': 0
        })

    return render(request, 'quality_control/ticket_detail.html', {
        'ticket': ticket,
        'ncrs': ncrs,
        'verdict_form': verdict_form,
        'page_title': f'QC Inspection: {ticket.ticket_number}'
    })


@login_required
def ncr_list(request):
    severity = request.GET.get('severity', '')
    status = request.GET.get('status', '')

    ncrs = NonConformanceReport.objects.select_related('ticket', 'reported_by').order_by('-created_at')
    if severity:
        ncrs = ncrs.filter(defect_severity=severity)
    if status:
        ncrs = ncrs.filter(status=status)

    return render(request, 'quality_control/ncr_list.html', {
        'ncrs': ncrs,
        'selected_severity': severity,
        'selected_status': status,
        'page_title': 'Non-Conformance Reports (NCR) & Defect Tracking'
    })


@login_required
def ncr_detail(request, pk):
    ncr = get_object_or_404(NonConformanceReport.objects.select_related('ticket', 'reported_by'), pk=pk)
    capas = ncr.capas.all()

    if request.method == 'POST':
        capa_form = CAPAActionForm(request.POST)
        if capa_form.is_valid():
            c = capa_form.save(commit=False)
            c.ncr = ncr
            c.save()
            ncr.status = 'CAPA_INITIATED'
            ncr.save()
            messages.success(request, "CAPA Action Plan logged.")
            return redirect('quality_control:ncr_detail', pk=ncr.id)
    else:
        capa_form = CAPAActionForm(initial={'target_due_date': timezone.now().date() + timezone.timedelta(days=14)})

    return render(request, 'quality_control/ncr_detail.html', {
        'ncr': ncr,
        'capas': capas,
        'capa_form': capa_form,
        'page_title': f'NCR Review: {ncr.ncr_number}'
    })
