from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import (
    VendorPortalProfile, SupplierBidRfq, SupplierBidSubmission,
    AdvanceShippingNotice, VendorInvoiceUpload, ThreeWayMatchVerification
)
from .forms import VendorProfileForm, BidSubmissionForm, ASNCreateForm, VendorInvoiceForm
from .services import VendorBiddingEngine, ASNReceiptMatcher, ThreeWayMatchEngine
from purchasing.models import Supplier, PurchaseOrder

@login_required
def dashboard_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    vendor_profiles = VendorPortalProfile.objects.filter(organization=org) if org else VendorPortalProfile.objects.all()

    total_vendors = vendor_profiles.count()
    open_rfqs_count = SupplierBidRfq.objects.filter(status='OPEN')
    if org:
        open_rfqs_count = open_rfqs_count.filter(organization=org)
    open_rfqs_count = open_rfqs_count.count()

    active_asns = AdvanceShippingNotice.objects.filter(status__in=['DISPATCHED', 'IN_TRANSIT'])
    if org:
        active_asns = active_asns.filter(organization=org)
    active_asns_count = active_asns.count()

    pending_matches = VendorInvoiceUpload.objects.filter(match_status='PENDING_MATCH')
    if org:
        pending_matches = pending_matches.filter(organization=org)
    pending_matches_count = pending_matches.count()

    recent_rfqs = SupplierBidRfq.objects.filter(organization=org) if org else SupplierBidRfq.objects.all()
    recent_rfqs = recent_rfqs.order_by('-created_at')[:5]

    recent_asns = AdvanceShippingNotice.objects.filter(organization=org) if org else AdvanceShippingNotice.objects.all()
    recent_asns = recent_asns.order_by('-created_at')[:5]

    recent_invoices = VendorInvoiceUpload.objects.filter(organization=org) if org else VendorInvoiceUpload.objects.all()
    recent_invoices = recent_invoices.order_by('-created_at')[:5]

    context = {
        'total_vendors': total_vendors,
        'open_rfqs_count': open_rfqs_count,
        'active_asns_count': active_asns_count,
        'pending_matches_count': pending_matches_count,
        'recent_rfqs': recent_rfqs,
        'recent_asns': recent_asns,
        'recent_invoices': recent_invoices,
    }
    return render(request, 'vendor_portal/dashboard.html', context)


@login_required
def rfq_list_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    rfqs = SupplierBidRfq.objects.filter(organization=org) if org else SupplierBidRfq.objects.all()
    context = {'rfqs': rfqs}
    return render(request, 'vendor_portal/rfq_list.html', context)


@login_required
def bid_submit_view(request, pk):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    rfq = get_object_or_404(SupplierBidRfq, pk=pk)

    if request.method == 'POST':
        form = BidSubmissionForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.organization = org if org else rfq.organization
            bid.save()
            VendorBiddingEngine.calculate_bid_score(bid)
            messages.success(request, f"Bid of ${bid.total_bid_amount} submitted successfully for RFQ {rfq.rfq_number}!")
            return redirect('vendor_portal:rfq_list')
    else:
        form = BidSubmissionForm(initial={'rfq': rfq})

    submissions = rfq.submissions.all()
    context = {
        'rfq': rfq,
        'form': form,
        'submissions': submissions
    }
    return render(request, 'vendor_portal/bid_form.html', context)


@login_required
def asn_list_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    asns = AdvanceShippingNotice.objects.filter(organization=org) if org else AdvanceShippingNotice.objects.all()
    context = {'asns': asns}
    return render(request, 'vendor_portal/asn_list.html', context)


@login_required
def asn_create_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None

    if request.method == 'POST':
        form = ASNCreateForm(request.POST)
        if form.is_valid():
            asn = form.save(commit=False)
            asn.organization = org if org else asn.vendor.organization
            asn.save()
            ASNReceiptMatcher.process_asn_delivery(asn)
            messages.success(request, f"ASN #{asn.asn_number} created and inventory receipt auto-generated!")
            return redirect('vendor_portal:asn_list')
    else:
        form = ASNCreateForm()

    context = {'form': form}
    return render(request, 'vendor_portal/asn_form.html', context)


@login_required
def invoice_list_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    invoices = VendorInvoiceUpload.objects.filter(organization=org) if org else VendorInvoiceUpload.objects.all()
    context = {'invoices': invoices}
    return render(request, 'vendor_portal/invoice_upload.html', context)


@login_required
def invoice_upload_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None

    if request.method == 'POST':
        form = VendorInvoiceForm(request.POST)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.organization = org if org else inv.vendor.organization
            inv.save()
            match_res = ThreeWayMatchEngine.verify_invoice(inv)
            messages.success(request, f"Invoice #{inv.invoice_number} uploaded! 3-Way Match Status: {match_res.get_match_status_display()}")
            return redirect('vendor_portal:invoice_list')
    else:
        form = VendorInvoiceForm()

    context = {'form': form}
    return render(request, 'vendor_portal/invoice_upload.html', context)


@login_required
def three_way_match_view(request):
    org = request.user.organization if hasattr(request.user, 'organization') and request.user.organization else None
    matches = ThreeWayMatchVerification.objects.filter(organization=org) if org else ThreeWayMatchVerification.objects.all()
    context = {'matches': matches}
    return render(request, 'vendor_portal/three_way_match.html', context)
