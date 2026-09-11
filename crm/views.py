from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from .models import Lead, Opportunity, Contact, Company, Activity, Campaign
from .forms import LeadForm, OpportunityForm, ContactForm, CompanyForm, ActivityForm
from audit.middleware import log_audit_event
from notifications.models import notify_user

@login_required
def crm_dashboard(request):
    total_leads = Lead.objects.count()
    new_leads = Lead.objects.filter(status='NEW').count()
    active_opps = Opportunity.objects.exclude(stage__in=['CLOSED_WON', 'CLOSED_LOST'])
    total_pipeline_val = active_opps.aggregate(Sum('amount'))['amount__sum'] or 0
    won_revenue = Opportunity.objects.filter(stage='CLOSED_WON').aggregate(Sum('amount'))['amount__sum'] or 0
    avg_deal_size = Opportunity.objects.aggregate(Avg('amount'))['amount__avg'] or 0

    recent_leads = Lead.objects.select_related('assigned_to').order_by('-created_at')[:5]
    recent_activities = Activity.objects.select_related('created_by', 'opportunity', 'lead').order_by('-created_at')[:5]

    # Pipeline stages breakdown
    stage_breakdown = []
    for stage_code, stage_name in Opportunity.STAGE_CHOICES:
        stage_opps = Opportunity.objects.filter(stage=stage_code)
        count = stage_opps.count()
        val = stage_opps.aggregate(Sum('amount'))['amount__sum'] or 0
        stage_breakdown.append({
            'code': stage_code,
            'name': stage_name,
            'count': count,
            'value': val
        })

    return render(request, 'crm/dashboard.html', {
        'total_leads': total_leads,
        'new_leads': new_leads,
        'pipeline_value': total_pipeline_val,
        'won_revenue': won_revenue,
        'avg_deal_size': avg_deal_size,
        'recent_leads': recent_leads,
        'recent_activities': recent_activities,
        'stage_breakdown': stage_breakdown,
    })

@login_required
def lead_list(request):
    leads = Lead.objects.select_related('assigned_to', 'campaign').all()
    status_filter = request.GET.get('status')
    search = request.GET.get('q')

    if status_filter:
        leads = leads.filter(status=status_filter)
    if search:
        leads = leads.filter(models.Q(first_name__icontains=search) | models.Q(last_name__icontains=search) | models.Q(company_name__icontains=search) | models.Q(email__icontains=search))

    paginator = Paginator(leads, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/lead_list.html', {
        'page_obj': page_obj,
        'statuses': Lead.STATUS_CHOICES,
        'selected_status': status_filter,
        'search_query': search,
    })

@login_required
def lead_create(request):
    form = LeadForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        lead = form.save()
        log_audit_event(request.user, 'CREATE', 'Lead', lead.id, str(lead), request=request)
        if lead.assigned_to and lead.assigned_to != request.user:
            notify_user(
                recipient=lead.assigned_to,
                title="New Lead Assigned",
                message=f"You have been assigned new lead: {lead.first_name} {lead.last_name} ({lead.company_name or 'N/A'})",
                category='SALES',
                link=f"/crm/leads/{lead.id}/"
            )
        messages.success(request, f'Lead {lead} created successfully!')
        return redirect('crm:lead_list')
    return render(request, 'crm/lead_form.html', {'form': form, 'title': 'Add New Lead'})

@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead.objects.select_related('assigned_to', 'campaign'), pk=pk)
    activities = lead.activities.select_related('created_by').all()
    activity_form = ActivityForm(request.POST or None)

    if request.method == 'POST' and 'add_activity' in request.POST:
        if activity_form.is_valid():
            act = activity_form.save(commit=False)
            act.lead = lead
            act.created_by = request.user
            act.save()
            log_audit_event(request.user, 'CREATE', 'Activity', act.id, str(act), request=request)
            messages.success(request, 'Activity recorded!')
            return redirect('crm:lead_detail', pk=pk)

    return render(request, 'crm/lead_detail.html', {
        'lead': lead,
        'activities': activities,
        'activity_form': activity_form,
    })

@login_required
def lead_convert(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if lead.status == 'CONVERTED':
        messages.warning(request, 'This lead has already been converted.')
        return redirect('crm:lead_detail', pk=pk)

    if request.method == 'POST':
        # Create company
        company = None
        if lead.company_name:
            company, _ = Company.objects.get_or_create(
                name=lead.company_name,
                defaults={'phone': lead.phone, 'email': lead.email}
            )

        # Create contact
        contact, _ = Contact.objects.get_or_create(
            email=lead.email,
            defaults={
                'company': company,
                'first_name': lead.first_name,
                'last_name': lead.last_name,
                'phone': lead.phone,
                'is_primary_contact': True
            }
        )

        # Create Opportunity
        opp = Opportunity.objects.create(
            name=f"{lead.company_name or lead.first_name + ' ' + lead.last_name} Deal",
            company=company,
            contact=contact,
            lead=lead,
            stage='QUALIFICATION',
            amount=lead.estimated_budget or 5000.00,
            probability=25,
            expected_close_date=timezone.now().date() + timezone.timedelta(days=30),
            assigned_to=lead.assigned_to or request.user,
            campaign=lead.campaign
        )

        lead.status = 'CONVERTED'
        lead.save(update_fields=['status'])

        log_audit_event(request.user, 'UPDATE', 'Lead', lead.id, str(lead), request=request, description=f"Converted lead to Opportunity #{opp.id}")
        messages.success(request, f'Lead successfully converted to Opportunity: {opp.name}!')
        return redirect('crm:pipeline')

    return render(request, 'crm/lead_convert_confirm.html', {'lead': lead})

@login_required
def pipeline_view(request):
    stages = Opportunity.STAGE_CHOICES
    pipeline_data = []

    for code, label in stages:
        opps = Opportunity.objects.filter(stage=code).select_related('company', 'contact', 'assigned_to')
        total_val = opps.aggregate(Sum('amount'))['amount__sum'] or 0
        pipeline_data.append({
            'code': code,
            'label': label,
            'opportunities': opps,
            'total_value': total_val,
            'count': opps.count()
        })

    return render(request, 'crm/pipeline.html', {'pipeline_data': pipeline_data})

@login_required
def opportunity_create(request):
    form = OpportunityForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        opp = form.save()
        log_audit_event(request.user, 'CREATE', 'Opportunity', opp.id, str(opp), request=request)
        messages.success(request, f'Opportunity {opp.name} created successfully!')
        return redirect('crm:pipeline')
    return render(request, 'crm/opportunity_form.html', {'form': form, 'title': 'Create Deal / Opportunity'})

@login_required
def contact_list(request):
    contacts = Contact.objects.select_related('company').all()
    paginator = Paginator(contacts, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'crm/contact_list.html', {'page_obj': page_obj})

@login_required
def company_list(request):
    companies = Company.objects.annotate(contacts_count=Count('contacts'), opps_count=Count('opportunities')).all()
    paginator = Paginator(companies, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'crm/company_list.html', {'page_obj': page_obj})
