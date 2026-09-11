import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.db.models import Count, Sum, Q

from .models import (
    ShippingCarrier, FreightRateMatrix, FreightConsignment,
    FreightConsignmentItem, TransitMilestoneCheckpoint, FreightShippingInvoice
)
from .forms import (
    ShippingCarrierForm, FreightConsignmentBookingForm, TransitMilestoneForm
)
from .services import (
    VolumetricWeightCalculator, FreightRatingEngine, ConsignmentTrackingService
)


@login_required
def logistics_dashboard(request):
    total_shipments = FreightConsignment.objects.count()
    in_transit = FreightConsignment.objects.filter(status__in=['BOOKED', 'PICKED_UP', 'AT_TERMINAL', 'IN_CUSTOMS', 'IN_TRANSIT', 'OUT_FOR_DELIVERY'])
    delivered_count = FreightConsignment.objects.filter(status='DELIVERED').count()
    customs_holds = FreightConsignment.objects.filter(status__in=['IN_CUSTOMS', 'EXCEPTION']).count()

    recent_consignments = FreightConsignment.objects.select_related('carrier', 'customer').order_by('-booking_date')[:10]
    carriers = ShippingCarrier.objects.filter(is_active=True)

    context = {
        'total_shipments': total_shipments,
        'active_in_transit': in_transit.count(),
        'delivered_count': delivered_count,
        'customs_holds': customs_holds,
        'recent_consignments': recent_consignments,
        'carriers': carriers,
        'page_title': 'Global Logistics, Freight Forwarding & 3PL Hub',
    }
    return render(request, 'logistics_3pl/dashboard.html', context)


@login_required
def consignment_list(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    mode = request.GET.get('mode', '')

    consignments = FreightConsignment.objects.select_related('carrier', 'customer').order_by('-booking_date')

    if query:
        consignments = consignments.filter(
            Q(tracking_number__icontains=query) |
            Q(shipper_name__icontains=query) |
            Q(consignee_name__icontains=query) |
            Q(origin_hub__icontains=query) |
            Q(destination_hub__icontains=query)
        )
    if status:
        consignments = consignments.filter(status=status)
    if mode:
        consignments = consignments.filter(transport_mode=mode)

    return render(request, 'logistics_3pl/consignment_list.html', {
        'consignments': consignments[:100],
        'query': query,
        'selected_status': status,
        'selected_mode': mode,
        'page_title': 'Freight Consignments & Manifests'
    })


@login_required
def consignment_create(request):
    if request.method == 'POST':
        form = FreightConsignmentBookingForm(request.POST)
        if form.is_valid():
            consignment = form.save(commit=False)
            consignment.tracking_number = f"NEX-{consignment.carrier.code[:3]}-{timezone.now().strftime('%y%m%d%H%M')}"
            consignment.status = 'BOOKED'
            consignment.save()

            # Generate initial milestone checkpoint
            ConsignmentTrackingService.add_milestone_event(
                consignment=consignment,
                location_city=consignment.origin_hub,
                facility_name="Origin Freight Terminal",
                status_title="Booking Confirmed / Manifest Created",
                description=f"Electronic shipping instruction generated for {consignment.carrier.name}.",
                user=request.user
            )

            # Auto-generate freight invoice
            FreightRatingEngine.generate_shipping_quote_and_invoice(consignment, user=request.user)

            messages.success(request, f"Consignment #{consignment.tracking_number} booked successfully.")
            return redirect('logistics_3pl:consignment_detail', pk=consignment.id)
    else:
        form = FreightConsignmentBookingForm(initial={
            'origin_hub': 'JFK Air Cargo Terminal (New York)',
            'destination_hub': 'Frankfurt Cargo City South (FRA)',
            'actual_gross_weight_kg': Decimal('50.00'),
            'volumetric_weight_kg': Decimal('60.00'),
            'chargeable_weight_kg': Decimal('60.00'),
            'total_volume_cbm': Decimal('0.300'),
            'declared_customs_value': Decimal('1500.00'),
        })

    return render(request, 'logistics_3pl/consignment_form.html', {'form': form, 'page_title': 'Book New Freight Shipment'})


@login_required
def consignment_detail(request, pk):
    consignment = get_object_or_404(
        FreightConsignment.objects.select_related('carrier', 'customer'),
        pk=pk
    )
    checkpoints = consignment.checkpoints.all().order_by('-timestamp')
    packages = consignment.packages.all()
    invoice = getattr(consignment, 'freight_invoice', None)
    milestone_form = TransitMilestoneForm()

    return render(request, 'logistics_3pl/consignment_detail.html', {
        'consignment': consignment,
        'checkpoints': checkpoints,
        'packages': packages,
        'invoice': invoice,
        'milestone_form': milestone_form,
        'page_title': f'Shipment Tracking - {consignment.tracking_number}'
    })


@login_required
def consignment_add_milestone(request, pk):
    consignment = get_object_or_404(FreightConsignment, pk=pk)
    if request.method == 'POST':
        form = TransitMilestoneForm(request.POST)
        if form.is_valid():
            ConsignmentTrackingService.add_milestone_event(
                consignment=consignment,
                location_city=form.cleaned_data['location_city'],
                facility_name=form.cleaned_data['facility_name'],
                status_title=form.cleaned_data['status_title'],
                description=form.cleaned_data['description'],
                latitude=form.cleaned_data.get('latitude'),
                longitude=form.cleaned_data.get('longitude'),
                user=request.user
            )
            messages.success(request, "Transit milestone checkpoint added.")
    return redirect('logistics_3pl:consignment_detail', pk=consignment.id)


@login_required
def consignment_awb_slip(request, pk):
    consignment = get_object_or_404(FreightConsignment.objects.select_related('carrier', 'customer'), pk=pk)
    invoice = getattr(consignment, 'freight_invoice', None)

    return render(request, 'logistics_3pl/air_waybill_slip.html', {
        'consignment': consignment,
        'invoice': invoice,
        'page_title': f'Air Waybill / BOL - {consignment.tracking_number}'
    })


@login_required
def carrier_list(request):
    carriers = ShippingCarrier.objects.all()
    return render(request, 'logistics_3pl/carrier_list.html', {
        'carriers': carriers,
        'page_title': 'Shipping Carriers & 3PL Partners'
    })


@login_required
def carrier_create(request):
    if request.method == 'POST':
        form = ShippingCarrierForm(request.POST)
        if form.is_valid():
            c = form.save()
            messages.success(request, f"Carrier {c.name} ({c.code}) created successfully.")
            return redirect('logistics_3pl:carrier_list')
    else:
        form = ShippingCarrierForm()
    return render(request, 'logistics_3pl/carrier_form.html', {'form': form, 'page_title': 'Add Shipping Carrier'})


# ---------------- API Endpoints ----------------

@login_required
@require_GET
def api_calculate_volumetric(request):
    l = float(request.GET.get('l', 0))
    w = float(request.GET.get('w', 0))
    h = float(request.GET.get('h', 0))
    actual = float(request.GET.get('gross_weight', 0))
    mode = request.GET.get('mode', 'AIR_FREIGHT')

    res = VolumetricWeightCalculator.calculate_package_metrics(l, w, h, actual, mode)
    return JsonResponse({
        'success': True,
        'volume_cbm': float(res['volume_cbm']),
        'actual_weight_kg': float(res['actual_weight_kg']),
        'volumetric_weight_kg': float(res['volumetric_weight_kg']),
        'chargeable_weight_kg': float(res['chargeable_weight_kg'])
    })
