from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from taxation.models import TaxJurisdiction, HSNSACCode, EUVATRule, USStateNexusRate
from taxation.services import (
    GSTCalculationEngine, EInvoicePayloadBuilder, EWayBillGenerator,
    EUVATOSSValidator, USNexusTaxCalculator
)


class TaxationTestCase(TestCase):
    def setUp(self):
        self.jurisdiction_in = TaxJurisdiction.objects.create(
            country='IN', name='India GST', code='IN-GST', is_default=True
        )
        self.jurisdiction_us = TaxJurisdiction.objects.create(
            country='US', name='US Sales Tax', code='US-SALES'
        )

        self.hsn = HSNSACCode.objects.create(
            code="84713010",
            description="Laptops and Personal Computers",
            code_type="HSN",
            standard_gst_rate=Decimal('18.00')
        )

        self.eu_rule_de = EUVATRule.objects.create(
            member_state_code='DE',
            country_name='Germany',
            standard_vat_rate=Decimal('19.00'),
            reduced_vat_rate=Decimal('7.00')
        )

        self.us_rule_ny = USStateNexusRate.objects.create(
            state_code='NY',
            state_name='New York',
            state_sales_tax_rate=Decimal('4.00'),
            avg_local_sales_tax_rate=Decimal('4.50')
        )

    def test_gst_intra_state_vs_inter_state(self):
        # Intra-state: 27 (MH) to 27 (MH) -> CGST 9% + SGST 9%
        intra = GSTCalculationEngine.calculate_gst(taxable_amount=1000, total_rate_pct=18, seller_state_code='27', buyer_state_code='27')
        self.assertEqual(intra['tax_type'], 'INTRA_STATE_CGST_SGST')
        self.assertEqual(intra['cgst_amount'], Decimal('90.00'))
        self.assertEqual(intra['sgst_amount'], Decimal('90.00'))
        self.assertEqual(intra['igst_amount'], Decimal('0.00'))
        self.assertEqual(intra['total_amount'], Decimal('1180.00'))

        # Inter-state: 27 (MH) to 29 (KA) -> IGST 18%
        inter = GSTCalculationEngine.calculate_gst(taxable_amount=1000, total_rate_pct=18, seller_state_code='27', buyer_state_code='29')
        self.assertEqual(inter['tax_type'], 'INTER_STATE_IGST')
        self.assertEqual(inter['cgst_amount'], Decimal('0.00'))
        self.assertEqual(inter['sgst_amount'], Decimal('0.00'))
        self.assertEqual(inter['igst_amount'], Decimal('180.00'))
        self.assertEqual(inter['total_amount'], Decimal('1180.00'))

    def test_einvoice_irn_generation(self):
        einvoice = EInvoicePayloadBuilder.generate_einvoice_irn(
            invoice_number="INV-2026-001",
            invoice_date=timezone.now().date(),
            seller_gstin="27AABCN1234F1Z1",
            buyer_gstin="29XYZAB5678G1Z2",
            taxable_value=5000.00,
            tax_amount=900.00,
            total_value=5900.00
        )
        self.assertEqual(len(einvoice.irn_hash), 64)
        self.assertEqual(einvoice.status, 'ACTIVE')
        self.assertIn("SellerGSTIN", einvoice.qr_code_payload)

    def test_eway_bill_generation_and_validity(self):
        ewb = EWayBillGenerator.generate_eway_bill(
            document_number="INV-2026-002",
            document_type="TAX_INVOICE",
            total_invoice_value=150000.00,
            from_pincode="400001",
            to_pincode="560001",
            distance_km=980,
            vehicle_number="MH04AB1234"
        )
        self.assertTrue(ewb.ewb_number.isdigit())
        self.assertEqual(ewb.status, 'GENERATED')
        # 980 km -> (980 + 199)//200 = 5 days validity
        delta = (ewb.valid_until - ewb.valid_from).days
        self.assertEqual(delta, 5)

    def test_eu_vat_oss_and_reverse_charge(self):
        # B2C: Standard 19%
        b2c = EUVATOSSValidator.calculate_eu_vat('DE', Decimal('100.00'), is_b2b=False)
        self.assertEqual(b2c['vat_amount'], Decimal('19.00'))
        self.assertFalse(b2c['is_reverse_charge'])

        # B2B with valid VIES: Reverse Charge (0%)
        b2b = EUVATOSSValidator.calculate_eu_vat('DE', Decimal('100.00'), is_b2b=True, is_vies_valid=True)
        self.assertEqual(b2b['vat_amount'], Decimal('0.00'))
        self.assertTrue(b2b['is_reverse_charge'])

    def test_us_sales_tax(self):
        res = USNexusTaxCalculator.calculate_us_sales_tax('NY', Decimal('100.00'))
        self.assertEqual(res['state_tax_amount'], Decimal('4.00'))
        self.assertEqual(res['local_tax_amount'], Decimal('4.50'))
        self.assertEqual(res['total_tax'], Decimal('8.50'))
        self.assertEqual(res['total_amount'], Decimal('108.50'))
