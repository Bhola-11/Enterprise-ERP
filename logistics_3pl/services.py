from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db import transaction
from .models import (
    ShippingCarrier, FreightRateMatrix, FreightConsignment,
    FreightConsignmentItem, TransitMilestoneCheckpoint, FreightShippingInvoice
)
from accounting.models import JournalEntry, JournalItem, Account


class VolumetricWeightCalculator:
    """
    International standard dimensional weight calculation engine:
    - IATA Air Freight: (L x W x H in cm) / 5000 (or 167 kg/CBM)
    - Road Freight LTL: (L x W x H in cm) / 3000 (or 333 kg/CBM)
    - Ocean Freight LCL: Revenue Ton / 1000 kg per CBM (W/M Rule)
    """

    @staticmethod
    def calculate_package_metrics(length_cm, width_cm, height_cm, gross_weight_kg, transport_mode='AIR_FREIGHT'):
        l = Decimal(str(length_cm))
        w = Decimal(str(width_cm))
        h = Decimal(str(height_cm))
        actual_kg = Decimal(str(gross_weight_kg))

        # Volume in CBM (m3)
        volume_cbm = ((l * w * h) / Decimal('1000000.00')).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

        if 'AIR' in transport_mode.upper():
            # IATA Divisor 5000
            dim_kg = ((l * w * h) / Decimal('5000.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif 'ROAD' in transport_mode.upper():
            # Road Divisor 3000
            dim_kg = ((l * w * h) / Decimal('3000.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif 'OCEAN' in transport_mode.upper():
            # Ocean 1 CBM = 1000 kg
            dim_kg = (volume_cbm * Decimal('1000.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            dim_kg = ((l * w * h) / Decimal('5000.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        chargeable_kg = max(actual_kg, dim_kg)

        return {
            'volume_cbm': volume_cbm,
            'actual_weight_kg': actual_kg,
            'volumetric_weight_kg': dim_kg,
            'chargeable_weight_kg': chargeable_kg
        }


class FreightRatingEngine:
    """
    Computes landed shipping costs, fuel surcharges, customs brokerage, and generates billing invoices.
    """

    @classmethod
    @transaction.atomic
    def generate_shipping_quote_and_invoice(cls, consignment, user=None):
        carrier = consignment.carrier
        chargeable_kg = consignment.chargeable_weight_kg

        rate_card = FreightRateMatrix.objects.filter(
            carrier=carrier,
            is_active=True
        ).first()

        if rate_card:
            rate_per_kg = rate_card.rate_per_kg
            min_charge = rate_card.minimum_charge
            fuel_pct = rate_card.fuel_surcharge_percentage
            security_fee_per_kg = rate_card.security_surcharge_per_kg
        else:
            rate_per_kg = Decimal('5.00')
            min_charge = Decimal('50.00')
            fuel_pct = Decimal('10.00')
            security_fee_per_kg = Decimal('0.10')

        calc_freight = (chargeable_kg * rate_per_kg).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        base_freight = max(min_charge, calc_freight)
        fuel_surcharge = (base_freight * (fuel_pct / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        security_fee = (chargeable_kg * security_fee_per_kg).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        customs_brokerage = Decimal('45.00') if consignment.declared_customs_value > Decimal('250.00') else Decimal('0.00')
        origin_handling = Decimal('25.00')
        destination_handling = Decimal('30.00')
        insurance = (consignment.declared_customs_value * Decimal('0.015')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        subtotal = base_freight + fuel_surcharge + security_fee + customs_brokerage + origin_handling + destination_handling + insurance
        tax_amount = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        grand_total = subtotal + tax_amount

        inv_num = f"FRT-INV-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        invoice = FreightShippingInvoice.objects.create(
            invoice_number=inv_num,
            consignment=consignment,
            base_freight_charge=base_freight,
            fuel_surcharge_amount=fuel_surcharge,
            customs_brokerage_fee=customs_brokerage,
            origin_handling_fee=origin_handling,
            destination_handling_fee=destination_handling,
            insurance_fee=insurance,
            tax_amount=tax_amount,
            grand_total=grand_total,
            status='PENDING'
        )

        return invoice


class ConsignmentTrackingService:
    """
    Records and broadcasts multi-leg transit milestone checkpoints.
    """

    @staticmethod
    def add_milestone_event(consignment, location_city, facility_name, status_title, description="", latitude=None, longitude=None, user=None):
        checkpoint = TransitMilestoneCheckpoint.objects.create(
            consignment=consignment,
            timestamp=timezone.now(),
            location_city=location_city,
            facility_name=facility_name,
            status_title=status_title,
            description=description,
            latitude=latitude,
            longitude=longitude,
            updated_by=user
        )

        # Update consignment status mapping
        title_lower = status_title.lower()
        if 'delivered' in title_lower or 'pod' in title_lower:
            consignment.status = 'DELIVERED'
            consignment.actual_delivery_date = timezone.now()
        elif 'out for delivery' in title_lower:
            consignment.status = 'OUT_FOR_DELIVERY'
        elif 'customs' in title_lower:
            consignment.status = 'IN_CUSTOMS'
        elif 'in transit' in title_lower or 'departed' in title_lower or 'flight' in title_lower:
            consignment.status = 'IN_TRANSIT'
        elif 'picked up' in title_lower:
            consignment.status = 'PICKED_UP'

        consignment.save()
        return checkpoint
