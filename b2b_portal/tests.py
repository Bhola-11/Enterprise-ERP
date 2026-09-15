from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from organizations.models import Organization
from sales.models import Customer, Quotation
from inventory.models import Product, ProductCategory, UnitOfMeasure
from b2b_portal.models import B2BAccount, B2BCatalogPriceTier, QuoteApprovalRequest, SelfServiceOrder
from b2b_portal.services import B2BPricingEngine, CreditCheckService, DigitalPaymentGateway, QuoteConversionService

class B2BPortalTestCase(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Test Corp')
        self.category = ProductCategory.objects.create(name='Electronics', code='ELEC')
        self.uom = UnitOfMeasure.objects.create(name='Pieces', symbol='pcs')
        self.product = Product.objects.create(
            category=self.category,
            uom=self.uom,
            name='Enterprise Server Blade',
            sku='SRV-BLADE-01',
            selling_price=Decimal('1000.00'),
            cost_price=Decimal('600.00')
        )
        self.customer = Customer.objects.create(
            first_name='Apex',
            last_name='Cloud',
            company_name='Apex Cloud Solutions',
            email='procurement@apexcloud.io',
            phone='5125550100',
            billing_address='100 Cloud Blvd',
            city='Austin'
        )
        self.b2b_account = B2BAccount.objects.create(
            organization=self.org,
            customer=self.customer,
            account_number='B2B-APEX-001',
            credit_limit=Decimal('50000.00'),
            credit_balance_used=Decimal('10000.00')
        )

    def test_b2b_pricing_tier_resolution(self):
        B2BCatalogPriceTier.objects.create(
            organization=self.org,
            b2b_account=self.b2b_account,
            product=self.product,
            min_quantity=5,
            tier_unit_price=Decimal('850.00'),
            discount_percentage=Decimal('5.00')
        )
        pricing = B2BPricingEngine.resolve_item_price(self.b2b_account, self.product, quantity=10)
        self.assertEqual(pricing['unit_price'], Decimal('850.00'))
        self.assertEqual(pricing['final_unit_price'], Decimal('807.50'))
        self.assertEqual(pricing['subtotal'], Decimal('8075.00'))

    def test_credit_check_evaluation(self):
        eval_ok = CreditCheckService.evaluate_credit_availability(self.b2b_account, Decimal('20000.00'))
        self.assertTrue(eval_ok['has_sufficient_credit'])
        self.assertEqual(eval_ok['available_credit'], Decimal('40000.00'))

        eval_fail = CreditCheckService.evaluate_credit_availability(self.b2b_account, Decimal('45000.00'))
        self.assertFalse(eval_fail['has_sufficient_credit'])
        self.assertEqual(eval_fail['shortfall'], Decimal('5000.00'))

    def test_digital_payment_gateway(self):
        tx = DigitalPaymentGateway.execute_payment(
            b2b_account=self.b2b_account,
            amount=Decimal('5000.00'),
            gateway='STRIPE'
        )
        self.assertEqual(tx.status, 'CAPTURED')
        self.assertEqual(self.b2b_account.credit_balance_used, Decimal('5000.00'))

    def test_quote_approval_and_conversion(self):
        quote = Quotation.objects.create(
            customer=self.customer,
            quote_number='QT-TEST-001',
            date=timezone.now().date(),
            expiry_date=timezone.now().date() + timezone.timedelta(days=30),
            subtotal=Decimal('8000.00'),
            tax_amount=Decimal('640.00'),
            total_amount=Decimal('8640.00'),
            status='DRAFT'
        )
        approval = QuoteApprovalRequest.objects.create(
            organization=self.org,
            b2b_account=self.b2b_account,
            quotation=quote,
            request_token='test-tok-123'
        )
        so = QuoteConversionService.approve_and_convert(approval, customer_notes='Approved by VP of Procurement')
        self.assertEqual(approval.status, 'CONVERTED')
        self.assertIsNotNone(approval.resulting_sales_order)
        self.assertEqual(so.total_amount, Decimal('8640.00'))
