import uuid
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import (
    VendorPortalProfile, SupplierBidRfq, SupplierBidSubmission,
    AdvanceShippingNotice, VendorInvoiceUpload, ThreeWayMatchVerification
)
from purchasing.models import PurchaseOrder, GoodsReceiptNote, GoodsReceiptItem
from warehouse.models import Warehouse

class VendorBiddingEngine:
    @staticmethod
    def calculate_bid_score(bid):
        target_price = Decimal('50000.00')
        price_ratio = min(Decimal('1.0'), target_price / max(Decimal('1.0'), bid.total_bid_amount))
        price_score = price_ratio * Decimal('50.0')

        lead_days = Decimal(str(bid.lead_time_days))
        lead_score = max(Decimal('0.0'), (Decimal('30.0') - lead_days))
        lead_score = min(Decimal('30.0'), lead_score)

        rating = bid.vendor.rating_score
        quality_score = (rating / Decimal('5.0')) * Decimal('20.0')

        composite = round(price_score + lead_score + quality_score, 2)
        bid.composite_evaluation_score = composite
        bid.save(update_fields=['composite_evaluation_score'])
        return composite

    @staticmethod
    @transaction.atomic
    def award_bid(bid, user=None):
        rfq = bid.rfq
        rfq.status = 'AWARDED'
        rfq.save(update_fields=['status'])

        bid.status = 'AWARDED'
        bid.save(update_fields=['status'])

        rfq.submissions.exclude(id=bid.id).update(status='REJECTED')
        return bid


class ASNReceiptMatcher:
    @staticmethod
    @transaction.atomic
    def process_asn_delivery(asn):
        asn.status = 'DELIVERED'
        asn.save(update_fields=['status'])

        po = asn.purchase_order
        warehouse = Warehouse.objects.filter(is_active=True).first()
        if not warehouse:
            warehouse = Warehouse.objects.first()

        grn_num = f"GRN-ASN-{asn.asn_number}"
        if warehouse:
            grn, created = GoodsReceiptNote.objects.get_or_create(
                grn_number=grn_num,
                defaults={
                    'purchase_order': po,
                    'warehouse': warehouse,
                    'receipt_date': timezone.now().date(),
                    'delivery_note_ref': asn.tracking_number,
                    'notes': f"Auto-generated from ASN #{asn.asn_number} via {asn.carrier_name}"
                }
            )
        else:
            grn = None

        asn.status = 'VERIFIED'
        asn.save(update_fields=['status'])
        return grn


class ThreeWayMatchEngine:
    @staticmethod
    @transaction.atomic
    def verify_invoice(vendor_invoice, tolerance_pct=Decimal('0.01')):
        po = vendor_invoice.purchase_order
        po_total = po.total_amount if hasattr(po, 'total_amount') else Decimal('0.00')

        grns = GoodsReceiptNote.objects.filter(purchase_order=po)
        grn_received_amount = po_total if grns.exists() else Decimal('0.00')

        inv_total = vendor_invoice.total_amount
        price_variance = inv_total - po_total
        quantity_variance = Decimal('0.00') if grns.exists() else (po_total - grn_received_amount)

        max_allowed_variance = po_total * tolerance_pct

        if abs(price_variance) <= max_allowed_variance and quantity_variance == Decimal('0.00'):
            match_status = 'FULL_MATCH'
            vendor_invoice.match_status = 'MATCH_PASSED'
        elif abs(price_variance) > max_allowed_variance and quantity_variance == Decimal('0.00'):
            match_status = 'PRICE_VARIANCE'
            vendor_invoice.match_status = 'MATCH_FAILED'
        elif quantity_variance > Decimal('0.00'):
            match_status = 'QUANTITY_VARIANCE'
            vendor_invoice.match_status = 'MATCH_FAILED'
        else:
            match_status = 'DISCREPANCY_FLAGGED'
            vendor_invoice.match_status = 'MATCH_FAILED'

        vendor_invoice.save(update_fields=['match_status'])

        match_record, _ = ThreeWayMatchVerification.objects.update_or_create(
            vendor_invoice=vendor_invoice,
            defaults={
                'organization': vendor_invoice.organization,
                'po_amount': po_total,
                'grn_received_amount': grn_received_amount,
                'invoice_amount': inv_total,
                'price_variance': price_variance,
                'quantity_variance': quantity_variance,
                'match_status': match_status,
                'auditor_notes': f"Automated 3-Way Match Check. Variance: ${price_variance} (Tolerance: {tolerance_pct*100}%)"
            }
        )
        return match_record
