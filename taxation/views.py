from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.db.models import Sum, Count, Q

from .models import (
    TaxJurisdiction, HSNSACCode, GSTTaxRate, EWayBillRecord,
    EInvoiceIRN, EUVATRule, USStateNexusRate, TaxFilingReturn
)
from .forms import (
    TaxJurisdictionForm, HSNSACCodeForm, EWayBillGenerateForm,
    TaxFilingReturnForm
)
from .services import (
    GSTCalculationEngine, EWayBillGenerator, EInvoicePayloadBuilder,
    EUVATOSSValidator, USNexusTaxCalculator
)
from sales.models import Invoice


@login_required
def tax_dashboard(request):
    jurisdictions = TaxJurisdiction.objects.all()
    hsns = HSNSACCode.objects.all()
    recent_ewb = EWayBillRecord.objects.all()[:5]
    recent_irn = EInvoiceIRN.objects.all()[:5]
    recent_filings = TaxFilingReturn.objects.select_related('jurisdiction').all()[:5]

    total_ewb = EWayBillRecord.objects.count()
    total_irn = EInvoiceIRN.objects.count()
    total_filings = TaxFilingReturn.objects.count()

    context = {
        'jurisdictions': jurisdictions,
        'hsns_count': hsns.count(),
        'recent_ewb': recent_ewb,
        'recent_irn': recent_irn,
        'recent_filings': recent_filings,
        'total_ewb': total_ewb,
        'total_irn': total_irn,
        'total_filings': total_filings,
        'page_title': 'Global Tax & Localization Hub',
    }
    return render(request, 'taxation/dashboard.html', context)


@login_required
def jurisdiction_list(request):
    jurisdictions = TaxJurisdiction.objects.all()
    return render(request, 'taxation/jurisdiction_list.html', {
        'jurisdictions': jurisdictions,
        'page_title': 'Tax Jurisdictions & Regulatory Authorities'
    })


@login_required
def jurisdiction_create(request):
    if request.method == 'POST':
        form = TaxJurisdictionForm(request.POST)
        if form.is_valid():
            j = form.save()
            messages.success(request, f"Jurisdiction {j.name} created successfully.")
            return redirect('taxation:jurisdiction_list')
    else:
        form = TaxJurisdictionForm()
    return render(request, 'taxation/jurisdiction_form.html', {'form': form, 'page_title': 'Add Tax Jurisdiction'})


@login_required
def hsn_list(request):
    query = request.GET.get('q', '')
    hsns = HSNSACCode.objects.all()
    if query:
        hsns = hsns.filter(Q(code__icontains=query) | Q(description__icontains=query))

    return render(request, 'taxation/hsn_list.html', {
        'hsns': hsns[:100],
        'query': query,
        'page_title': 'HSN / SAC Master Code Directory'
    })


@login_required
def hsn_create(request):
    if request.method == 'POST':
        form = HSNSACCodeForm(request.POST)
        if form.is_valid():
            hsn = form.save()
            messages.success(request, f"HSN/SAC Code {hsn.code} added successfully.")
            return redirect('taxation:hsn_list')
    else:
        form = HSNSACCodeForm()
    return render(request, 'taxation/hsn_form.html', {'form': form, 'page_title': 'Add HSN / SAC Code'})


@login_required
def eway_bill_list(request):
    ewbs = EWayBillRecord.objects.all().order_by('-created_at')
    return render(request, 'taxation/eway_bill_list.html', {
        'ewbs': ewbs,
        'page_title': 'e-Way Bills & Transit Consignments'
    })


@login_required
def eway_bill_create(request):
    if request.method == 'POST':
        form = EWayBillGenerateForm(request.POST)
        if form.is_valid():
            ewb = EWayBillGenerator.generate_eway_bill(
                document_number=form.cleaned_data['document_number'],
                document_type=form.cleaned_data['document_type'],
                total_invoice_value=form.cleaned_data['total_invoice_value'],
                from_pincode=form.cleaned_data['from_pincode'],
                to_pincode=form.cleaned_data['to_pincode'],
                distance_km=form.cleaned_data['distance_km'],
                vehicle_number=form.cleaned_data['vehicle_number'],
                transporter_id=form.cleaned_data['transporter_id'],
                transporter_name=form.cleaned_data['transporter_name'],
                user=request.user
            )
            messages.success(request, f"e-Way Bill #{ewb.ewb_number} generated successfully with validity until {ewb.valid_until.strftime('%Y-%m-%d %H:%M')}.")
            return redirect('taxation:eway_bill_detail', pk=ewb.id)
    else:
        form = EWayBillGenerateForm()

    return render(request, 'taxation/eway_bill_form.html', {'form': form, 'page_title': 'Generate e-Way Bill'})


@login_required
def eway_bill_detail(request, pk):
    ewb = get_object_or_404(EWayBillRecord, pk=pk)
    return render(request, 'taxation/eway_bill_detail.html', {
        'ewb': ewb,
        'page_title': f'e-Way Bill #{ewb.ewb_number}'
    })


@login_required
def einvoice_list(request):
    einvoices = EInvoiceIRN.objects.all().order_by('-created_at')
    return render(request, 'taxation/einvoice_list.html', {
        'einvoices': einvoices,
        'page_title': 'e-Invoicing IRN Portal'
    })


@login_required
def einvoice_detail(request, pk):
    irn_rec = get_object_or_404(EInvoiceIRN, pk=pk)
    return render(request, 'taxation/einvoice_detail.html', {
        'irn_rec': irn_rec,
        'page_title': f'e-Invoice IRN Details'
    })


@login_required
def tax_filing_list(request):
    filings = TaxFilingReturn.objects.select_related('jurisdiction', 'filed_by').all().order_by('-period_end')
    return render(request, 'taxation/tax_filing_list.html', {
        'filings': filings,
        'page_title': 'Tax Filings & Statutory Returns'
    })


@login_required
def tax_filing_create(request):
    if request.method == 'POST':
        form = TaxFilingReturnForm(request.POST)
        if form.is_valid():
            filing = form.save(commit=False)
            filing.filed_by = request.user
            filing.filed_at = timezone.now() if filing.status == 'FILED' else None
            filing.save()
            messages.success(request, f"Tax return filing for {filing.get_return_type_display()} recorded successfully.")
            return redirect('taxation:tax_filing_list')
    else:
        form = TaxFilingReturnForm()

    return render(request, 'taxation/tax_filing_form.html', {'form': form, 'page_title': 'Record Tax Filing Return'})


@login_required
def gstr1_generator(request):
    today = timezone.now().date()
    start_date = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', today.strftime('%Y-%m-%d'))

    summary = GSTCalculationEngine.generate_gstr1_summary(start_date, end_date)

    return render(request, 'taxation/gstr1_report.html', {
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
        'page_title': 'GSTR-1 Outward Supplies Summary'
    })


# ---------------- JSON API Endpoints ----------------

@login_required
@require_GET
def api_calculate_tax(request):
    country = request.GET.get('country', 'IN').upper()
    taxable_amount = Decimal(request.GET.get('amount', '0'))

    if country == 'IN':
        rate = Decimal(request.GET.get('rate', '18.0'))
        seller_state = request.GET.get('seller_state', '27')
        buyer_state = request.GET.get('buyer_state', '27')
        res = GSTCalculationEngine.calculate_gst(taxable_amount, rate, seller_state, buyer_state)
        return JsonResponse({'success': True, 'data': {
            'taxable_amount': float(res['taxable_amount']),
            'cgst_amount': float(res['cgst_amount']),
            'sgst_amount': float(res['sgst_amount']),
            'igst_amount': float(res['igst_amount']),
            'total_tax': float(res['total_tax']),
            'total_amount': float(res['total_amount']),
            'tax_type': res['tax_type']
        }})
    elif country == 'US':
        state = request.GET.get('state', 'NY')
        res = USNexusTaxCalculator.calculate_us_sales_tax(state, taxable_amount)
        return JsonResponse({'success': True, 'data': {
            'state_tax': float(res['state_tax_amount']),
            'local_tax': float(res['local_tax_amount']),
            'total_tax': float(res['total_tax']),
            'total_amount': float(res['total_amount']),
        }})
    elif country == 'EU':
        state = request.GET.get('member_state', 'DE')
        is_b2b = request.GET.get('is_b2b') == 'true'
        res = EUVATOSSValidator.calculate_eu_vat(state, taxable_amount, is_b2b=is_b2b, is_vies_valid=True)
        return JsonResponse({'success': True, 'data': {
            'vat_rate': float(res['vat_rate']),
            'vat_amount': float(res['vat_amount']),
            'total_amount': float(res['total_amount']),
            'is_reverse_charge': res['is_reverse_charge']
        }})
    else:
        return JsonResponse({'success': False, 'message': f'Unsupported jurisdiction {country}'}, status=400)
