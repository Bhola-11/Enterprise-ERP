from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from quality_control.models import (
    InspectionPlan, InspectionCharacteristic, QualityInspectionTicket,
    NonConformanceReport, CAPAAction
)
from quality_control.services import SamplingEngine, QualityDispositionService

User = get_user_model()

class QualityControlTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='qc_inspector', email='qc@nexora.io', password='Password123!', role='OFFICER')
        self.plan = InspectionPlan.objects.create(
            code='QC-PLAN-RAW', name='Inward Metal Sheet Inspection',
            category='INWARD_GRN', sampling_standard='AQL_2_5', is_active=True
        )
        self.char1 = InspectionCharacteristic.objects.create(
            plan=self.plan, parameter_name='Thickness', measurement_unit='mm',
            min_acceptable_value=Decimal('2.950'), max_acceptable_value=Decimal('3.050'), is_critical=True
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_sampling_size_calculation(self):
        # Lot of 100 -> AQL 2.5 Normal table sample size = 20
        sz = SamplingEngine.compute_sample_size(100, 'AQL_2_5')
        self.assertEqual(sz, 20)

    def test_rejection_spawns_ncr(self):
        ticket = QualityInspectionTicket.objects.create(
            ticket_number='QC-TEST-001', plan=self.plan, reference_code='GRN-2026-999',
            lot_size=100, sample_size=20, status='PENDING'
        )
        # Record 18 passed, 2 rejected
        QualityDispositionService.record_inspection_verdict(ticket, 18, 2, "Thickness under tolerance", user=self.user)
        ticket.refresh_from_db()
        self.assertEqual(ticket.disposition, 'REJECTED')
        self.assertEqual(ticket.ncrs.count(), 1)
        ncr = ticket.ncrs.first()
        self.assertEqual(ncr.defect_severity, 'MAJOR')

    def test_views(self):
        res = self.client.get(reverse('quality_control:dashboard'))
        self.assertEqual(res.status_code, 200)

        res_plans = self.client.get(reverse('quality_control:plan_list'))
        self.assertEqual(res_plans.status_code, 200)
