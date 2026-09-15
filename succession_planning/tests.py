from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from hr.models import Employee, Department, Designation
from organizations.models import Organization, Branch
from succession_planning.models import CriticalRolePosition, TalentProfile, SuccessionPlan
from succession_planning.services import NineBoxMatrixService, BenchStrengthService

User = get_user_model()

class SuccessionPlanningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='hr_director',
            email='hr_director@nexora.io',
            password='Password123!'
        )
        self.org = Organization.objects.create(name='Nexora Enterprise', currency='USD')
        self.branch = Branch.objects.create(organization=self.org, name='NYC HQ', code='HQ-NYC')
        self.dept = Department.objects.create(organization=self.org, name='Engineering R&D', code='ENG', branch=self.branch)
        self.des_cto = Designation.objects.create(title='Chief Technology Officer', code='DES-CTO', department=self.dept)
        self.des_arch = Designation.objects.create(title='Principal Enterprise Architect', code='DES-ARCH', department=self.dept)

        self.emp_cto = Employee.objects.create(
            employee_id='EMP-SP-001',
            first_name='Evelyn',
            last_name='Reed',
            email='e.reed@nexora.io',
            department=self.dept,
            designation=self.des_cto,
            branch=self.branch,
            joining_date=date(2022, 1, 1),
            status='ACTIVE'
        )
        self.emp_arch = Employee.objects.create(
            employee_id='EMP-SP-002',
            first_name='Marcus',
            last_name='Vance',
            email='m.vance@nexora.io',
            department=self.dept,
            designation=self.des_arch,
            branch=self.branch,
            joining_date=date(2023, 5, 1),
            status='ACTIVE'
        )

        self.role_cto = CriticalRolePosition.objects.create(
            title='Chief Technology Officer',
            position_code='CRIT-CTO-01',
            department=self.dept,
            current_incumbent=self.emp_cto,
            risk_of_vacancy='HIGH',
            impact_of_loss='CRITICAL',
            target_bench_strength=1
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_nine_box_quadrant_calculation(self):
        tp_star = TalentProfile.objects.create(
            employee=self.emp_cto,
            performance_rating='HIGH',
            potential_rating='HIGH',
            flight_risk='LOW'
        )
        self.assertEqual(tp_star.nine_box_quadrant, '3_3')

        tp_growth = TalentProfile.objects.create(
            employee=self.emp_arch,
            performance_rating='HIGH',
            potential_rating='MEDIUM',
            flight_risk='HIGH'
        )
        self.assertEqual(tp_growth.nine_box_quadrant, '3_2')

        grid = NineBoxMatrixService.get_full_matrix_grid()
        self.assertEqual(len(grid['3_3']['profiles']), 1)
        self.assertEqual(len(grid['3_2']['profiles']), 1)

    def test_succession_plan_and_bench_strength(self):
        self.assertEqual(self.role_cto.ready_now_count, 0)
        self.assertEqual(self.role_cto.bench_strength_status, 'AT_RISK')

        # Nominate Marcus as Ready Now
        SuccessionPlan.objects.create(
            critical_position=self.role_cto,
            successor_employee=self.emp_arch,
            readiness_level='READY_NOW',
            ranking_priority=1
        )
        self.assertEqual(self.role_cto.ready_now_count, 1)
        self.assertEqual(self.role_cto.bench_strength_status, 'HEALTHY')

        kpis = BenchStrengthService.get_enterprise_pipeline_kpis()
        self.assertEqual(kpis['total_critical_roles'], 1)
        self.assertEqual(kpis['roles_healthy'], 1)
        self.assertEqual(kpis['roles_at_risk'], 0)
        self.assertEqual(kpis['pipeline_coverage_rate'], 100.0)

    def test_views(self):
        res_dash = self.client.get(reverse('succession_planning:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_grid = self.client.get(reverse('succession_planning:nine_box_matrix'))
        self.assertEqual(res_grid.status_code, 200)

        res_roles = self.client.get(reverse('succession_planning:role_list'))
        self.assertEqual(res_roles.status_code, 200)

        res_role_detail = self.client.get(reverse('succession_planning:role_detail', args=[self.role_cto.id]))
        self.assertEqual(res_role_detail.status_code, 200)

        res_talent = self.client.get(reverse('succession_planning:talent_list'))
        self.assertEqual(res_talent.status_code, 200)
