from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounting.models import Account
from fixed_assets_depr.models import DepreciableAsset, AssetDepreciationPeriod, AssetImpairmentRecord, AssetDisposalRecord
from fixed_assets_depr.services import DepreciationEngine, AssetImpairmentService, AssetDisposalService

User = get_user_model()

class FixedAssetsDepreciationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin_fa',
            email='admin_fa@nexora.erp',
            password='Password123!'
        )
        self.client = Client()
        self.client.force_login(self.user)

        self.gl_asset = Account.objects.create(code='15000', name='Machinery & Robotics', account_type='ASSET', balance=Decimal('500000.00'), is_active=True)
        self.gl_accum = Account.objects.create(code='15900', name='Accumulated Depr - Machinery', account_type='ASSET', balance=Decimal('0.00'), is_active=True)
        self.gl_exp = Account.objects.create(code='61000', name='Depreciation Expense', account_type='EXPENSE', balance=Decimal('0.00'), is_active=True)

    def test_straight_line_schedule_generation(self):
        asset = DepreciableAsset.objects.create(
            asset_tag='FA-ROBOT-001',
            asset_name='Automated Assembly Arm 6-Axis',
            category_name='Robotics',
            acquisition_date=date(2026, 1, 1),
            acquisition_cost=Decimal('120000.00'),
            salvage_value=Decimal('0.00'),
            useful_life_months=60,
            depreciation_method='STRAIGHT_LINE',
            asset_gl_account=self.gl_asset,
            accumulated_depr_gl_account=self.gl_accum,
            depreciation_expense_gl_account=self.gl_exp
        )
        periods_count = DepreciationEngine.generate_full_schedule(asset)
        self.assertEqual(periods_count, 60)
        self.assertEqual(asset.depreciation_schedule.count(), 60)

        # First month check: 120,000 / 60 = 2,000.00
        p1 = asset.depreciation_schedule.first()
        self.assertEqual(p1.depreciation_amount, Decimal('2000.00'))
        self.assertEqual(p1.closing_book_value, Decimal('118000.00'))

        # Post period 1
        je = DepreciationEngine.post_depreciation_period(p1, user=self.user)
        self.assertIsNotNone(je)
        self.assertTrue(p1.is_posted)
        asset.refresh_from_db()
        self.assertEqual(asset.accumulated_depreciation, Decimal('2000.00'))
        self.assertEqual(asset.net_book_value, Decimal('118000.00'))

    def test_double_declining_depreciation(self):
        asset = DepreciableAsset.objects.create(
            asset_tag='FA-CNC-002',
            asset_name='5-Axis CNC Milling Center',
            category_name='Industrial Machining',
            acquisition_date=date(2026, 1, 1),
            acquisition_cost=Decimal('240000.00'),
            salvage_value=Decimal('20000.00'),
            useful_life_months=60,
            depreciation_method='DOUBLE_DECLINING',
            asset_gl_account=self.gl_asset,
            accumulated_depr_gl_account=self.gl_accum,
            depreciation_expense_gl_account=self.gl_exp
        )
        periods_count = DepreciationEngine.generate_full_schedule(asset)
        self.assertEqual(periods_count, 60)
        p1 = asset.depreciation_schedule.first()
        # DDB monthly rate = 2.0 / 5 / 12 = 0.40 / 12 = 0.03333333... * 240,000 = 8,000.00
        self.assertEqual(p1.depreciation_amount, Decimal('8000.00'))
        self.assertEqual(p1.closing_book_value, Decimal('232000.00'))

    def test_ias36_impairment(self):
        asset = DepreciableAsset.objects.create(
            asset_tag='FA-SERVER-003',
            asset_name='Edge AI Inference Compute Cluster',
            category_name='IT Hardware',
            acquisition_date=date(2026, 1, 1),
            acquisition_cost=Decimal('80000.00'),
            net_book_value=Decimal('80000.00'),
            salvage_value=Decimal('5000.00'),
            useful_life_months=36,
            depreciation_method='STRAIGHT_LINE',
            asset_gl_account=self.gl_asset,
            accumulated_depr_gl_account=self.gl_accum,
            depreciation_expense_gl_account=self.gl_exp
        )
        # Impair down to 50,000 recoverable amount
        imp = AssetImpairmentService.record_impairment(
            asset=asset,
            recoverable_amt=Decimal('50000.00'),
            reason_text='Next-gen architecture rendered hardware semi-obsolete',
            user=self.user
        )
        self.assertEqual(imp.impairment_loss, Decimal('30000.00'))
        asset.refresh_from_db()
        self.assertEqual(asset.net_book_value, Decimal('50000.00'))
        self.assertEqual(asset.status, 'IMPAIRED')

    def test_asset_disposal_gain_loss(self):
        asset = DepreciableAsset.objects.create(
            asset_tag='FA-VEHICLE-004',
            asset_name='EV Delivery Van Fleet Unit 1',
            category_name='Vehicles',
            acquisition_date=date(2026, 1, 1),
            acquisition_cost=Decimal('50000.00'),
            net_book_value=Decimal('35000.00'),
            salvage_value=Decimal('5000.00'),
            useful_life_months=48,
            depreciation_method='STRAIGHT_LINE',
            asset_gl_account=self.gl_asset,
            accumulated_depr_gl_account=self.gl_accum,
            depreciation_expense_gl_account=self.gl_exp
        )
        # Sell for 40,000 => Gain of 5,000
        disp = AssetDisposalService.record_disposal(
            asset=asset,
            sale_proceeds=Decimal('40000.00'),
            buyer_name='Apex Logistics Corp',
            user=self.user
        )
        self.assertEqual(disp.gain_loss_amount, Decimal('5000.00'))
        asset.refresh_from_db()
        self.assertEqual(asset.net_book_value, Decimal('0.00'))
        self.assertEqual(asset.status, 'DISPOSED')

    def test_http_views(self):
        asset = DepreciableAsset.objects.create(
            asset_tag='FA-TEST-005',
            asset_name='Test Asset',
            category_name='Testing',
            acquisition_date=date(2026, 1, 1),
            acquisition_cost=Decimal('10000.00'),
            salvage_value=Decimal('0.00'),
            useful_life_months=12,
            asset_gl_account=self.gl_asset,
            accumulated_depr_gl_account=self.gl_accum,
            depreciation_expense_gl_account=self.gl_exp
        )
        res_dash = self.client.get(reverse('fixed_assets_depr:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_list = self.client.get(reverse('fixed_assets_depr:asset_list'))
        self.assertEqual(res_list.status_code, 200)

        res_detail = self.client.get(reverse('fixed_assets_depr:asset_detail', args=[asset.id]))
        self.assertEqual(res_detail.status_code, 200)
