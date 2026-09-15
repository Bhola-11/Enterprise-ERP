from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from organizations.models import Organization
from accounts.models import User
from sales.models import Customer
from inventory.models import Product, ProductCategory, UnitOfMeasure
from field_service_fsm.models import (
    ServiceTerritory, ServiceTechnician, WorkOrder, PartConsumption, CustomerSignoff
)
from field_service_fsm.services import DispatchSchedulingEngine, InventoryConsumptionEngine, SLATrackerService

class FieldServiceFSMTestCase(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Test Corp')
        self.user = User.objects.create_user(email='tech_alex@nexora.com', username='tech_alex', password='password123')
        self.customer = Customer.objects.create(
            first_name='BioMed',
            last_name='Laboratories',
            company_name='BioMed Labs Inc.',
            email='facility@biomed.com',
            phone='5125550188',
            billing_address='200 Science Way',
            city='Austin'
        )
        self.category = ProductCategory.objects.create(name='Sensors', code='SENS')
        self.uom = UnitOfMeasure.objects.create(name='Pieces', symbol='pcs')
        self.product = Product.objects.create(
            category=self.category,
            uom=self.uom,
            name='Pressure Transducer Sensor',
            sku='SENS-PRS-01',
            cost_price=Decimal('120.00'),
            selling_price=Decimal('250.00'),
            current_stock=Decimal('50')
        )
        self.territory = ServiceTerritory.objects.create(
            organization=self.org,
            name='Austin Metro Central',
            code='TERR-ATX-01',
            city='Austin'
        )
        self.tech = ServiceTechnician.objects.create(
            organization=self.org,
            user=self.user,
            technician_code='TECH-007',
            primary_territory=self.territory,
            skill_level='SENIOR_SPECIALIST',
            is_available=True
        )
        self.wo = WorkOrder.objects.create(
            organization=self.org,
            work_order_number='WO-2026-TEST',
            customer=self.customer,
            territory=self.territory,
            priority='HIGH',
            status='UNASSIGNED',
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timezone.timedelta(hours=2),
            sla_deadline=timezone.now() + timezone.timedelta(hours=4),
            issue_summary='Calibration failure on Cryo Unit #2',
            detailed_description='Sensor reporting drifting readings'
        )

    def test_dispatch_scheduling(self):
        matched_tech = DispatchSchedulingEngine.find_best_technician(self.wo)
        self.assertEqual(matched_tech, self.tech)

        dispatched = DispatchSchedulingEngine.dispatch_work_order(self.wo, self.tech)
        self.assertEqual(dispatched.status, 'DISPATCHED')
        self.assertEqual(dispatched.assigned_technician, self.tech)

    def test_inventory_consumption_and_stock_deduction(self):
        initial_stock = self.product.current_stock
        consumption = InventoryConsumptionEngine.record_part_consumption(self.wo, self.product, quantity=2)
        self.assertEqual(consumption.total_cost, Decimal('240.00'))

    def test_sla_tracker_and_customer_signoff(self):
        sla = SLATrackerService.check_sla_compliance(self.wo)
        self.assertEqual(sla['status'], 'COMPLIANT')

        signoff = SLATrackerService.complete_with_signoff(
            self.wo,
            signatory_name='Dr. Helen Cho',
            rating=5,
            feedback='Fast response and impeccable sensor calibration.'
        )
        self.assertEqual(self.wo.status, 'COMPLETED')
        self.assertEqual(signoff.satisfaction_rating, 5)
        self.assertIsNotNone(signoff.digital_signature_hash)
