from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from organizations.models import Organization, Branch
from sales.models import Customer
from logistics_3pl.models import (
    ShippingCarrier, FreightRateMatrix, FreightConsignment,
    TransitMilestoneCheckpoint, FreightShippingInvoice
)
from logistics_3pl.services import VolumetricWeightCalculator, FreightRatingEngine, ConsignmentTrackingService

User = get_user_model()

class Logistics3PLTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='logistics_manager', email='logistics@nexora.io', password='Password123!', role='MANAGER')
        self.org = Organization.objects.create(name='Global Freight Corp')
        self.branch = Branch.objects.create(organization=self.org, name='Main Port Branch', code='LOG-01')
        self.customer = Customer.objects.create(
            first_name='Apex', last_name='Imports', email='logistics@apex.com', phone='+1-555-4321',
            tax_id='TAX-APEX-99', billing_address='100 Cargo Way', city='Miami'
        )
        self.carrier = ShippingCarrier.objects.create(
            name='DHL Global Forwarding',
            code='DHL-GF',
            carrier_type='AIR',
            is_active=True
        )
        self.rate = FreightRateMatrix.objects.create(
            carrier=self.carrier,
            transport_mode='AIR',
            origin_zone='USA',
            destination_zone='EUR',
            rate_per_kg=Decimal('8.50'),
            minimum_charge=Decimal('75.00'),
            fuel_surcharge_percentage=Decimal('15.00'),
            security_surcharge_per_kg=Decimal('0.25'),
            is_active=True
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_volumetric_weight_calculation(self):
        calc = VolumetricWeightCalculator.calculate_package_metrics(
            length_cm=100, width_cm=50, height_cm=40,
            gross_weight_kg=30, transport_mode='AIR_FREIGHT'
        )
        self.assertEqual(calc['volumetric_weight_kg'], Decimal('40.00'))
        self.assertEqual(calc['chargeable_weight_kg'], Decimal('40.00'))

    def test_consignment_creation_and_rating(self):
        consignment = FreightConsignment.objects.create(
            tracking_number='NEX-DHL-100200',
            carrier=self.carrier,
            customer=self.customer,
            transport_mode='AIR_FREIGHT',
            origin_hub='JFK',
            destination_hub='FRA',
            shipper_name='Apex Logistics',
            shipper_address='JFK Terminal 4',
            consignee_name='Berlin Import Hub',
            consignee_address='Cargo City FRA',
            actual_gross_weight_kg=Decimal('50.00'),
            volumetric_weight_kg=Decimal('40.00'),
            chargeable_weight_kg=Decimal('50.00'),
            total_volume_cbm=Decimal('0.200'),
            total_packages_count=2,
            declared_customs_value=Decimal('5000.00'),
            status='BOOKED'
        )
        invoice = FreightRatingEngine.generate_shipping_quote_and_invoice(consignment, user=self.user)
        self.assertIsNotNone(invoice)
        self.assertTrue(invoice.grand_total > Decimal('0'))

    def test_milestone_tracking(self):
        consignment = FreightConsignment.objects.create(
            tracking_number='NEX-DHL-300400',
            carrier=self.carrier,
            transport_mode='AIR_FREIGHT',
            origin_hub='ORD',
            destination_hub='LHR',
            shipper_name='Midwest Exporters',
            shipper_address='Chicago ORD',
            consignee_name='UK Logistics',
            consignee_address='London LHR',
            actual_gross_weight_kg=Decimal('100.00'),
            volumetric_weight_kg=Decimal('80.00'),
            chargeable_weight_kg=Decimal('100.00'),
            total_volume_cbm=Decimal('0.500'),
            total_packages_count=5,
            status='BOOKED'
        )
        checkpoint = ConsignmentTrackingService.add_milestone_event(
            consignment=consignment,
            location_city='Chicago',
            facility_name='ORD Cargo Gate 3',
            status_title='Departed Origin Terminal',
            description='Loaded on aircraft flight BA294',
            user=self.user
        )
        self.assertEqual(consignment.checkpoints.count(), 1)
        self.assertEqual(checkpoint.status_title, 'Departed Origin Terminal')

    def test_logistics_views(self):
        res_dash = self.client.get(reverse('logistics_3pl:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_list = self.client.get(reverse('logistics_3pl:consignment_list'))
        self.assertEqual(res_list.status_code, 200)
