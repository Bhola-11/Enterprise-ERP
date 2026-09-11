from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import SystemSetting, IntegrationConfig
from organizations.models import Organization, Branch, Department

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    org = Organization.objects.first()
    return render(request, 'core/landing.html', {'org': org})

@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = {
        'query': query,
        'contacts': [],
        'leads': [],
        'orders': [],
        'invoices': [],
        'products': [],
        'employees': [],
        'tickets': [],
        'projects': [],
        'assets': [],
    }

    if query and len(query) >= 2:
        from crm.models import Contact, Lead
        from sales.models import SalesOrder, Invoice
        from inventory.models import Product
        from hr.models import Employee
        from support.models import SupportTicket
        from projects.models import Project
        from assets.models import Asset

        results['contacts'] = Contact.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))[:5]
        results['leads'] = Lead.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(company_name__icontains=query))[:5]
        results['orders'] = SalesOrder.objects.filter(Q(order_number__icontains=query) | Q(customer__first_name__icontains=query) | Q(customer__last_name__icontains=query))[:5]
        results['invoices'] = Invoice.objects.filter(Q(invoice_number__icontains=query) | Q(customer__first_name__icontains=query))[:5]
        results['products'] = Product.objects.filter(Q(name__icontains=query) | Q(sku__icontains=query) | Q(barcode__icontains=query))[:5]
        results['employees'] = Employee.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(employee_id__icontains=query))[:5]
        results['tickets'] = SupportTicket.objects.filter(Q(ticket_id__icontains=query) | Q(subject__icontains=query))[:5]
        results['projects'] = Project.objects.filter(Q(name__icontains=query) | Q(code__icontains=query))[:5]
        results['assets'] = Asset.objects.filter(Q(name__icontains=query) | Q(asset_tag__icontains=query) | Q(serial_number__icontains=query))[:5]

    return render(request, 'core/search_results.html', results)

@login_required
def system_settings_view(request):
    settings_list = SystemSetting.objects.all()
    integrations = IntegrationConfig.objects.all()
    return render(request, 'core/settings.html', {
        'settings_list': settings_list,
        'integrations': integrations,
    })
