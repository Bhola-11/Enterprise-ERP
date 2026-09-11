from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from organizations.models import Organization, Branch
from accounting.models import Account
from real_estate_pms.models import (
    PropertyComplex, PropertyUnit, PropertyTenant, LeaseAgreement,
    TenantRentInvoice, MaintenanceWorkOrder
)
from real_estate_pms.services import LeaseManagementService, RentCollectionService

User = get_user_model()

class RealEstatePMSTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='property_mgr', email='pms@nexora.io', password='Password123!', role='MANAGER')
        self.org = Organization.objects.create(name='Empire Properties REIT')
        self.branch = Branch.objects.create(organization=self.org, name='Manhattan Tower Office', code='RE-01')
        self.cash_acc = Account.objects.create(
            code='1010', name='Cash Operating Account', account_type='ASSET', is_active=True
        )
        self.ar_acc = Account.objects.create(
            code='1130', name='Tenant Rent Receivable', account_type='ASSET', is_active=True
        )

        self.complex = PropertyComplex.objects.create(
            name='Midtown Executive Plaza', code='MEP-NY', property_type='COMMERCIAL_OFFICE',
            address='750 3rd Avenue', city='New York', state='NY', total_floors=25
        )
        self.unit = PropertyUnit.objects.create(
            complex=self.complex, unit_number='Suite 1400', floor_number=14, unit_type='OFFICE_SUITE',
            square_feet=Decimal('3500.00'), base_monthly_rent=Decimal('12000.00'),
            cam_fee_monthly=Decimal('1500.00'), security_deposit=Decimal('24000.00'),
            occupancy_status='VACANT'
        )
        self.tenant = PropertyTenant.objects.create(
            company_or_name='Apex Quantum AI Corp', contact_person='Dr. Lisa Chang',
            email='lisa@apexquantum.ai', phone='+1-212-555-9080', is_corporate=True
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_lease_activation_and_rent_roll(self):
        lease = LeaseAgreement.objects.create(
            lease_number='LSE-TEST-001', unit=self.unit, tenant=self.tenant,
            start_date='2026-01-01', end_date='2027-12-31', monthly_rent=Decimal('12000.00'),
            cam_fee_monthly=Decimal('1500.00'), security_deposit_held=Decimal('24000.00'),
            annual_escalation_pct=Decimal('5.00'), payment_due_day=1, status='DRAFT'
        )
        LeaseManagementService.activate_lease(lease)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.occupancy_status, 'LEASED')

        invoice = LeaseManagementService.generate_monthly_rent_invoice(lease, year=2026, month=10)
        self.assertEqual(invoice.total_amount, Decimal('13500.00'))

    def test_rent_collection_ledger_post(self):
        lease = LeaseAgreement.objects.create(
            lease_number='LSE-TEST-002', unit=self.unit, tenant=self.tenant,
            start_date='2026-01-01', end_date='2027-12-31', monthly_rent=Decimal('10000.00'),
            cam_fee_monthly=Decimal('1000.00'), security_deposit_held=Decimal('20000.00'),
            status='ACTIVE'
        )
        invoice = LeaseManagementService.generate_monthly_rent_invoice(lease, year=2026, month=10)
        RentCollectionService.record_rent_payment(
            invoice=invoice, amount=Decimal('11000.00'),
            reference_no='WIRE-CHASE-887766', user=self.user
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'PAID')
        self.assertEqual(invoice.balance_amount, Decimal('0.00'))
        self.assertIsNotNone(invoice.journal_entry)

    def test_views(self):
        res = self.client.get(reverse('real_estate_pms:dashboard'))
        self.assertEqual(res.status_code, 200)

        res_props = self.client.get(reverse('real_estate_pms:property_list'))
        self.assertEqual(res_props.status_code, 200)

        res_rentroll = self.client.get(reverse('real_estate_pms:rent_roll_report'))
        self.assertEqual(res_rentroll.status_code, 200)
