from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from organizations.models import Branch, Organization
from warehouse.models import Warehouse
from inventory.models import Product, ProductCategory, UnitOfMeasure
from sales.models import Customer
from pos.models import POSTerminal, POSSession, POSOrder, POSCouponPromotion
from pos.services import POSPricingEngine, POSOrderProcessor, POSSessionManager, POSThermalReceiptFormatter

User = get_user_model()


class POSTestCase(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Nexora Global Corp", currency="USD")
        self.branch = Branch.objects.create(organization=self.org, name="Downtown Flagship", code="DT01", city="New York")
        self.warehouse = Warehouse.objects.create(branch=self.branch, name="Main Retail Warehouse", code="WH-RET-01")
        self.user = User.objects.create_user(username="cashier1", email="cashier1@nexora.io", password="Password@123", role="STAFF")

        self.category = ProductCategory.objects.create(name="Electronics", code="ELEC")
        self.uom = UnitOfMeasure.objects.create(name="Piece", symbol="pcs")
        self.product1 = Product.objects.create(
            name="Wireless Mouse",
            sku="WM-100",
            barcode="8901234567890",
            category=self.category,
            uom=self.uom,
            cost_price=Decimal('15.00'),
            selling_price=Decimal('25.00'),
            current_stock=Decimal('100.00')
        )

        self.terminal = POSTerminal.objects.create(
            terminal_code="POS-01",
            name="Checkout Counter 1",
            branch=self.branch,
            warehouse=self.warehouse,
            status='ACTIVE'
        )

        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            tax_id="TAX-1234",
            billing_address="123 Main St",
            city="New York"
        )

    def test_pricing_engine(self):
        res = POSPricingEngine.calculate_line_item(unit_price=100, quantity=2, discount_pct=10, tax_rate=10)
        self.assertEqual(res['base_amount'], Decimal('200.00'))
        self.assertEqual(res['discount_amount'], Decimal('20.00'))
        self.assertEqual(res['taxable_amount'], Decimal('180.00'))
        self.assertEqual(res['tax_amount'], Decimal('18.00'))
        self.assertEqual(res['line_total'], Decimal('198.00'))

    def test_session_lifecycle_and_order_checkout(self):
        # 1. Open Session
        session = POSSessionManager.open_session(self.terminal, self.user, opening_cash=Decimal('150.00'))
        self.assertEqual(session.status, 'OPEN')
        self.assertEqual(session.expected_cash, Decimal('150.00'))

        # 2. Process Checkout
        items = [{
            'product_id': self.product1.id,
            'quantity': 2,
            'unit_price': 25.00,
            'discount_percentage': 0.0,
            'tax_rate': 10.0
        }]
        payments = [{
            'payment_method': 'CASH',
            'amount': 60.00
        }]

        order = POSOrderProcessor.process_checkout(
            session=session,
            cashier=self.user,
            items_data=items,
            payments_data=payments,
            customer=self.customer
        )

        self.assertEqual(order.status, 'COMPLETED')
        self.assertEqual(order.grand_total, Decimal('55.00'))  # 50 + 5 tax
        self.assertEqual(order.paid_amount, Decimal('60.00'))
        self.assertEqual(order.change_returned, Decimal('5.00'))

        # Stock deduction check
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.current_stock, Decimal('98.000'))

        # 3. Test Thermal Receipt generator
        receipt_text = POSThermalReceiptFormatter.generate_text_receipt(order)
        self.assertIn("NEXORA", receipt_text.upper())
        self.assertIn("Wireless Mouse", receipt_text)

        # 4. Close Session
        session.refresh_from_db()
        self.assertEqual(session.expected_cash, Decimal('205.00'))  # 150 float + 55 net cash
        closed_session = POSSessionManager.close_session(session, counted_cash=Decimal('205.00'), closed_by=self.user)
        self.assertEqual(closed_session.status, 'CLOSED')
        self.assertEqual(closed_session.cash_difference, Decimal('0.00'))

    def test_coupon_discount(self):
        coupon = POSCouponPromotion.objects.create(
            code="SAVE10",
            name="10% Discount",
            discount_type='PERCENT',
            discount_value=Decimal('10.00'),
            min_order_value=Decimal('50.00'),
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            usage_limit=100
        )
        res = POSPricingEngine.validate_and_apply_coupon("SAVE10", Decimal('100.00'))
        self.assertTrue(res['valid'])
        self.assertEqual(res['discount'], Decimal('10.00'))
