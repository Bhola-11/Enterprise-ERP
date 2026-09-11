from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Product, ProductCategory, UnitOfMeasure
from accounting.models import Account
from subcontracting.models import (
    SubcontractorVendor, SubcontractOrder, SubcontractMaterialDispatch,
    SubcontractGoodsReceipt
)
from subcontracting.services import SubcontractExecutionService

User = get_user_model()

class SubcontractingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='subcontract_mgr', email='subcontract@nexora.io', password='Password123!', role='MANAGER')
        self.cat = ProductCategory.objects.create(name='Precision Machining', code='CAT-MACHINING')
        self.uom = UnitOfMeasure.objects.create(name='Pieces', symbol='pcs')
        self.ap_acc = Account.objects.create(
            code='2010', name='Trade Accounts Payable', account_type='LIABILITY', is_active=True
        )
        self.cog_acc = Account.objects.create(
            code='5020', name='Outside Processing Expense', account_type='EXPENSE', is_active=True
        )

        self.fg = Product.objects.create(
            sku='ANODIZED-SHAFT', name='Anodized Drive Shaft', category=self.cat, uom=self.uom,
            selling_price=Decimal('120.00'), cost_price=Decimal('70.00')
        )
        self.raw_bar = Product.objects.create(
            sku='STEEL-BAR-100', name='Raw Steel Billet Bar', category=self.cat, uom=self.uom,
            selling_price=Decimal('40.00'), cost_price=Decimal('30.00')
        )

        self.vendor = SubcontractorVendor.objects.create(
            name='Precision Heat Treat & Anodizing LLC', code='VND-ANODIZE',
            facility_address='50 Industrial Loop, Detroit, MI', is_active=True
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_subcontract_dispatch_and_receipt_lifecycle(self):
        order = SubcontractOrder.objects.create(
            order_number='SCO-TEST-001', subcontractor=self.vendor, finished_product=self.fg,
            planned_quantity=Decimal('50.00'), unit_processing_rate=Decimal('15.00'),
            total_service_cost=Decimal('750.00'), expected_delivery_date='2026-10-15',
            status='DRAFT'
        )

        # Dispatch materials
        SubcontractExecutionService.dispatch_materials(
            order=order,
            items_data=[{'raw_material': self.raw_bar, 'quantity': Decimal('50.00')}],
            user=self.user
        )
        self.assertEqual(order.status, 'MATERIALS_DISPATCHED')
        self.assertEqual(order.dispatches.count(), 1)

        # Receive finished goods & post to GL
        sgrn = SubcontractExecutionService.receive_finished_goods(
            order=order, qty_received=Decimal('50.00'), qty_rejected=Decimal('0.00'),
            scrap_qty=Decimal('0.00'), vendor_dc_ref='DC-VND-8899', user=self.user
        )
        order.refresh_from_db()
        self.assertEqual(order.status, 'COMPLETED')
        self.assertEqual(sgrn.actual_yield_percentage, Decimal('100.00'))
        self.assertIsNotNone(sgrn.journal_entry)

    def test_views(self):
        res = self.client.get(reverse('subcontracting:dashboard'))
        self.assertEqual(res.status_code, 200)

        res_orders = self.client.get(reverse('subcontracting:order_list'))
        self.assertEqual(res_orders.status_code, 200)