from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from organizations.models import Organization, Branch
from purchasing.models import Supplier, PurchaseOrder, GoodsReceiptNote
from warehouse.models import Warehouse
from vendor_portal.models import (
    VendorPortalProfile, SupplierBidRfq, SupplierBidSubmission,
    AdvanceShippingNotice, VendorInvoiceUpload, ThreeWayMatchVerification
)
from vendor_portal.services import VendorBiddingEngine, ASNReceiptMatcher, ThreeWayMatchEngine

class VendorPortalTestCase(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Test Corp')
        self.branch = Branch.objects.create(
            organization=self.org,
            name='HQ Branch',
            code='BR-HQ-01',
            address='100 Main St',
            city='Austin'
        )
        self.supplier = Supplier.objects.create(
            name='Precision Microelectronics Corp',
            email='sales@precisionmicro.com',
            phone='5125550199',
            address='123 Tech Way',
            city='Austin'
        )
        self.warehouse = Warehouse.objects.create(
            branch=self.branch,
            name='Central Logistics Hub',
            code='WH-CENTRAL-01',
            address='100 Logistics Blvd',
            city='Austin'
        )
        self.vendor_profile = VendorPortalProfile.objects.create(
            organization=self.org,
            supplier=self.supplier,
            vendor_code='VEND-MICRO-001',
            rating_score=Decimal('4.80'),
            compliance_status='COMPLIANT'
        )
        self.rfq = SupplierBidRfq.objects.create(
            organization=self.org,
            rfq_number='RFQ-2026-TEST',
            title='High Precision Capacitors',
            description='Industrial grade bulk passives',
            target_delivery_date=timezone.now().date(),
            deadline=timezone.now() + timezone.timedelta(days=7),
            status='OPEN'
        )
        self.po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            po_number='PO-TEST-001',
            order_date=timezone.now().date(),
            subtotal=Decimal('50000.00'),
            tax_amount=Decimal('4000.00'),
            total_amount=Decimal('54000.00'),
            status='APPROVED'
        )

    def test_vendor_bidding_evaluation_and_award(self):
        bid = SupplierBidSubmission.objects.create(
            organization=self.org,
            rfq=self.rfq,
            vendor=self.vendor_profile,
            total_bid_amount=Decimal('48000.00'),
            lead_time_days=5,
            warranty_months=24
        )
        score = VendorBiddingEngine.calculate_bid_score(bid)
        self.assertGreater(score, Decimal('70.00'))

        awarded_bid = VendorBiddingEngine.award_bid(bid)
        self.assertEqual(awarded_bid.status, 'AWARDED')
        self.assertEqual(self.rfq.status, 'AWARDED')

    def test_asn_receipt_matcher(self):
        asn = AdvanceShippingNotice.objects.create(
            organization=self.org,
            vendor=self.vendor_profile,
            purchase_order=self.po,
            asn_number='ASN-TEST-99',
            carrier_name='FedEx Freight',
            tracking_number='FX-778899',
            estimated_arrival_date=timezone.now().date()
        )
        grn = ASNReceiptMatcher.process_asn_delivery(asn)
        self.assertEqual(asn.status, 'VERIFIED')
        self.assertIsNotNone(grn)

    def test_three_way_match_verification(self):
        GoodsReceiptNote.objects.create(
            grn_number='GRN-TEST-001',
            purchase_order=self.po,
            warehouse=self.warehouse,
            receipt_date=timezone.now().date()
        )
        inv = VendorInvoiceUpload.objects.create(
            organization=self.org,
            vendor=self.vendor_profile,
            purchase_order=self.po,
            invoice_number='INV-SUPP-001',
            subtotal_amount=Decimal('50000.00'),
            tax_amount=Decimal('4000.00'),
            total_amount=Decimal('54000.00')
        )
        match_rec = ThreeWayMatchEngine.verify_invoice(inv)
        self.assertEqual(inv.match_status, 'MATCH_PASSED')
        self.assertEqual(match_rec.match_status, 'FULL_MATCH')
        self.assertEqual(match_rec.price_variance, Decimal('0.00'))
