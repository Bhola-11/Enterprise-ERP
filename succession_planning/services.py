from django.db.models import Count, Q
from .models import CriticalRolePosition, TalentProfile, SuccessionPlan
from hr.models import Employee

class NineBoxMatrixService:
    @classmethod
    def get_full_matrix_grid(cls):
        """
        Builds the 3x3 grid matrix dictionary containing all employees grouped by quadrant.
        """
        profiles = TalentProfile.objects.select_related('employee', 'employee__department', 'employee__designation').all()
        
        matrix = {
            '1_3': {'label': 'Rough Diamond', 'category': 'High Potential', 'color': 'warning', 'profiles': []},
            '2_3': {'label': 'High Potential', 'category': 'Rising Star', 'color': 'success', 'profiles': []},
            '3_3': {'label': 'Star', 'category': 'Top Tier Talent', 'color': 'primary', 'profiles': []},
            '1_2': {'label': 'Inconsistent Performer', 'category': 'Development Dilemma', 'color': 'secondary', 'profiles': []},
            '2_2': {'label': 'Core Talent', 'category': 'Key Player', 'color': 'info', 'profiles': []},
            '3_2': {'label': 'High Performer', 'category': 'Growth Pillar', 'color': 'success', 'profiles': []},
            '1_1': {'label': 'Risk / Underperformer', 'category': 'Action Required', 'color': 'danger', 'profiles': []},
            '2_1': {'label': 'Effective Professional', 'category': 'Solid Specialist', 'color': 'secondary', 'profiles': []},
            '3_1': {'label': 'Trusted Specialist', 'category': 'Solid Anchor', 'color': 'info', 'profiles': []},
        }

        for p in profiles:
            q = p.nine_box_quadrant
            if q in matrix:
                matrix[q]['profiles'].append(p)

        return matrix


class BenchStrengthService:
    @classmethod
    def get_enterprise_pipeline_kpis(cls):
        total_roles = CriticalRolePosition.objects.filter(is_active=True).count()
        roles_with_ready_now = 0
        roles_at_risk = 0
        total_successors = SuccessionPlan.objects.filter(status='ACTIVE').count()
        high_flight_risk_stars = TalentProfile.objects.filter(flight_risk='HIGH', potential_rating='HIGH').count()

        roles = CriticalRolePosition.objects.filter(is_active=True).prefetch_related('succession_candidates')
        for r in roles:
            if r.ready_now_count >= r.target_bench_strength:
                roles_with_ready_now += 1
            elif r.ready_now_count == 0:
                roles_at_risk += 1

        coverage_rate = (roles_with_ready_now / total_roles * 100) if total_roles > 0 else 0

        return {
            'total_critical_roles': total_roles,
            'roles_healthy': roles_with_ready_now,
            'roles_at_risk': roles_at_risk,
            'total_successors_nominated': total_successors,
            'high_flight_risk_stars': high_flight_risk_stars,
            'pipeline_coverage_rate': round(coverage_rate, 1)
        }
