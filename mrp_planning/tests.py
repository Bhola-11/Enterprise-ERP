from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Product, ProductCategory, UnitOfMeasure
from organizations.models import Organization, Branch
from warehouse.models import Warehouse
from manufacturing.models import BillOfMaterials, BOMItem
from mrp_planning.models import MasterProductionSchedule, SafetyStockRule, MRPRun, MRPRequirementItem
from mrp_planning.services import BOMExplosionEngine, MRPCalculationEngine

User = get_user_model()

class MRPPlanningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='mrp_planner', email='mrp@nexora.io', password='Password123!', role='MANAGER')
        self.org = Organization.objects.create(name='Nexora Manufacturing LLC')
        self.branch = Branch.objects.create(organization=self.org, name='Detroit Plant', code='BR-DETROIT')
        self.cat = ProductCategory.objects.create(name='Robotics & Hardware', code='CAT-ROBOT')
        self.uom = UnitOfMeasure.objects.create(name='Pieces', symbol='pcs')
        self.wh = Warehouse.objects.create(branch=self.branch, name='Central Assembly Plant', code='WH-PLANT')

        self.fg = Product.objects.create(
            sku='ROBOT-ARM-01', name='Industrial Robotic Arm X1', category=self.cat, uom=self.uom,
            selling_price=Decimal('15000.00'), cost_price=Decimal('8000.00')
        )
        self.raw_motor = Product.objects.create(
            sku='SERVO-MTR-800', name='High-Torque Servo Motor', category=self.cat, uom=self.uom,
            selling_price=Decimal('500.00'), cost_price=Decimal('350.00')
        )
        self.raw_arm = Product.objects.create(
            sku='ALU-CAST-ARM', name='Cast Aluminum Armature', category=self.cat, uom=self.uom,
            selling_price=Decimal('300.00'), cost_price=Decimal('200.00')
        )

        self.bom = BillOfMaterials.objects.create(
            bom_number='BOM-ROBOT-01', finished_product=self.fg, quantity=Decimal('1.00')
        )
        BOMItem.objects.create(bom=self.bom, raw_material=self.raw_motor, quantity=Decimal('4.00'), scrap_percentage=Decimal('0.00'))
        BOMItem.objects.create(bom=self.bom, raw_material=self.raw_arm, quantity=Decimal('2.00'), scrap_percentage=Decimal('5.00'))

        self.client = Client()
        self.client.force_login(self.user)

    def test_bom_explosion(self):
        components = BOMExplosionEngine.explode_demand(self.fg, Decimal('10.00'))
        self.assertEqual(len(components), 2)
        motor_req = next(c for c in components if c['product'] == self.raw_motor)
        self.assertEqual(motor_req['quantity'], Decimal('40.00'))

    def test_mrp_calculation_run(self):
        mps = MasterProductionSchedule.objects.create(
            product=self.fg,
            period_start='2026-10-01',
            period_end='2026-10-31',
            forecast_demand_qty=Decimal('20.00'),
            confirmed_so_qty=Decimal('15.00'),
            planned_production_qty=Decimal('20.00'),
            status='APPROVED'
        )
        run = MRPCalculationEngine.execute_mrp_run(
            planning_horizon_days=90, include_forecast=True, include_safety_stock=True, user=self.user
        )
        self.assertEqual(run.status, 'COMPLETED')
        self.assertTrue(run.total_planned_orders_count > 0)

    def test_views(self):
        res = self.client.get(reverse('mrp_planning:dashboard'))
        self.assertEqual(res.status_code, 200)

        res_mps = self.client.get(reverse('mrp_planning:mps_list'))
        self.assertEqual(res_mps.status_code, 200)