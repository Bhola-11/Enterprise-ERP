from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from hr.models import Employee, Department, Designation
from organizations.models import Organization, Branch
from performance_appraisal.models import AppraisalCycle, CompetencyFramework, AppraisalSubmission, ContinuousFeedbackNote
from performance_appraisal.services import AppraisalScoringEngine

User = get_user_model()

class PerformanceAppraisalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='hr_appraisal_lead',
            email='hr_appraisal@nexora.io',
            password='Password123!'
        )
        self.org = Organization.objects.create(name='Nexora Global', currency='USD')
        self.branch = Branch.objects.create(organization=self.org, name='Global HQ', code='HQ-NYC')
        self.dept = Department.objects.create(organization=self.org, name='Product Design', code='DSG', branch=self.branch)
        self.des_lead = Designation.objects.create(title='Lead Product Designer', code='DES-DESG-01', department=self.dept)
        self.des_mgr = Designation.objects.create(title='Design Director', code='DES-DESG-02', department=self.dept)

        self.mgr = Employee.objects.create(
            employee_id='EMP-PA-001', first_name='Sarah', last_name='Connor',
            email='s.connor@nexora.io', department=self.dept, designation=self.des_mgr,
            branch=self.branch, joining_date=date(2022, 1, 1), status='ACTIVE'
        )
        self.emp = Employee.objects.create(
            employee_id='EMP-PA-002', first_name='David', last_name='Kim',
            email='d.kim@nexora.io', department=self.dept, designation=self.des_lead,
            branch=self.branch, joining_date=date(2023, 1, 1), status='ACTIVE'
        )

        self.cycle = AppraisalCycle.objects.create(
            name='FY 2026 Annual Performance Review',
            cycle_type='ANNUAL',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            self_review_deadline=date(2026, 11, 15),
            manager_review_deadline=date(2026, 11, 30),
            status='ACTIVE'
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_composite_scoring_engine(self):
        # Self = 4.0, Peer = 4.0, Manager = 5.0
        # Expected = (4.0 * 0.15) + (4.0 * 0.25) + (5.0 * 0.60) = 0.60 + 1.00 + 3.00 = 4.60 => OUTSTANDING
        sub = AppraisalSubmission.objects.create(
            cycle=self.cycle,
            employee=self.emp,
            manager=self.mgr,
            self_rating=Decimal('4.00'),
            self_summary='Delivered design system 2.0 ahead of schedule.',
            peer_average_rating=Decimal('4.00'),
            manager_rating=Decimal('5.00'),
            manager_summary='Extraordinary leadership across cross-functional engineering teams.'
        )

        score, band = AppraisalScoringEngine.calculate_composite_score(sub)
        self.assertEqual(score, Decimal('4.60'))
        self.assertEqual(band, 'OUTSTANDING')
        self.assertEqual(sub.status, 'COMPLETED')

        analytics = AppraisalScoringEngine.get_cycle_analytics(self.cycle)
        self.assertEqual(analytics['total_submissions'], 1)
        self.assertEqual(analytics['completed_count'], 1)
        self.assertEqual(analytics['band_distribution']['OUTSTANDING'], 1)

    def test_continuous_feedback(self):
        note = ContinuousFeedbackNote.objects.create(
            employee=self.emp,
            giver=self.mgr,
            feedback_type='PRAISE',
            title='Incredible Design Presentation to Board',
            content='David did an outstanding job leading the stakeholder demo today.'
        )
        self.assertIsNotNone(note.id)
        self.assertEqual(note.feedback_type, 'PRAISE')

    def test_views(self):
        sub = AppraisalSubmission.objects.create(
            cycle=self.cycle,
            employee=self.emp,
            manager=self.mgr
        )

        res_dash = self.client.get(reverse('performance_appraisal:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_cycles = self.client.get(reverse('performance_appraisal:cycle_list'))
        self.assertEqual(res_cycles.status_code, 200)

        res_detail = self.client.get(reverse('performance_appraisal:cycle_detail', args=[self.cycle.id]))
        self.assertEqual(res_detail.status_code, 200)

        res_sub = self.client.get(reverse('performance_appraisal:submission_detail', args=[sub.id]))
        self.assertEqual(res_sub.status_code, 200)

        res_fb = self.client.get(reverse('performance_appraisal:feedback_list'))
        self.assertEqual(res_fb.status_code, 200)
