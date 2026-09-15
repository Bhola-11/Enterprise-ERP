from django.db import models
from django.conf import settings
from hr.models import Employee, Department, Designation

class CriticalRolePosition(models.Model):
    RISK_LEVELS = [
        ('LOW', 'Low Vacancy Risk'),
        ('MEDIUM', 'Medium Vacancy Risk'),
        ('HIGH', 'High Vacancy Risk (Active Succession Priority)'),
        ('CRITICAL', 'Critical Immediate Vacancy Exposure'),
    ]
    IMPACT_LEVELS = [
        ('LOW', 'Low Operational Disruption'),
        ('MEDIUM', 'Moderate Operational Impact'),
        ('HIGH', 'High Strategic / Revenue Impact'),
        ('CRITICAL', 'Critical Mission-Essential Impact'),
    ]

    title = models.CharField(max_length=150)
    position_code = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='critical_roles')
    current_incumbent = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='incumbent_critical_roles')
    risk_of_vacancy = models.CharField(max_length=20, choices=RISK_LEVELS, default='MEDIUM')
    impact_of_loss = models.CharField(max_length=20, choices=IMPACT_LEVELS, default='HIGH')
    target_bench_strength = models.PositiveIntegerField(default=2, help_text="Number of ready successors required")
    required_competencies = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position_code']
        verbose_name = 'Critical Role & Key Position'
        verbose_name_plural = 'Critical Roles & Key Positions'

    def __str__(self):
        return f"{self.position_code}: {self.title} ({self.department.name})"

    @property
    def ready_now_count(self):
        return self.succession_candidates.filter(readiness_level='READY_NOW', status='ACTIVE').count()

    @property
    def bench_strength_status(self):
        rn = self.ready_now_count
        if rn >= self.target_bench_strength:
            return 'HEALTHY'
        elif rn > 0:
            return 'MODERATE'
        return 'AT_RISK'


class TalentProfile(models.Model):
    PERFORMANCE_LEVELS = [
        ('LOW', '1 - Low / Needs Development'),
        ('MEDIUM', '2 - Medium / Meets Expectations'),
        ('HIGH', '3 - High / Exceeds Expectations'),
    ]
    POTENTIAL_LEVELS = [
        ('LOW', '1 - Low / Lateral Role Fit'),
        ('MEDIUM', '2 - Medium / Growth Within Function'),
        ('HIGH', '3 - High / Cross-Functional Leadership Potential'),
    ]
    FLIGHT_RISKS = [
        ('LOW', 'Low Flight Risk'),
        ('MEDIUM', 'Medium Flight Risk'),
        ('HIGH', 'High Immediate Flight Risk'),
    ]
    NINE_BOX_CHOICES = [
        ('1_1', 'Risk / Underperformer (Low Perf, Low Pot)'),
        ('1_2', 'Inconsistent Performer (Low Perf, Med Pot)'),
        ('1_3', 'Rough Diamond (Low Perf, High Pot)'),
        ('2_1', 'Effective Professional (Med Perf, Low Pot)'),
        ('2_2', 'Core Talent / Key Player (Med Perf, Med Pot)'),
        ('2_3', 'High Potential / Rising Star (Med Perf, High Pot)'),
        ('3_1', 'Trusted Specialist / Solid Anchor (High Perf, Low Pot)'),
        ('3_2', 'High Performer (High Perf, Med Pot)'),
        ('3_3', 'Star / Top Tier Leadership (High Perf, High Pot)'),
    ]

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='talent_profile')
    performance_rating = models.CharField(max_length=10, choices=PERFORMANCE_LEVELS, default='MEDIUM')
    potential_rating = models.CharField(max_length=10, choices=POTENTIAL_LEVELS, default='MEDIUM')
    flight_risk = models.CharField(max_length=10, choices=FLIGHT_RISKS, default='LOW')
    retention_risk_reason = models.CharField(max_length=255, blank=True)
    nine_box_quadrant = models.CharField(max_length=10, choices=NINE_BOX_CHOICES, default='2_2')
    key_strengths = models.TextField(blank=True)
    career_aspirations = models.TextField(blank=True)
    last_calibrated_at = models.DateField(auto_now=True)

    class Meta:
        ordering = ['employee__first_name', 'employee__last_name']
        verbose_name = 'Employee 9-Box Talent Profile'
        verbose_name_plural = 'Employee 9-Box Talent Profiles'

    def __str__(self):
        return f"Talent Profile: {self.employee} ({self.get_nine_box_quadrant_display()})"

    def calculate_nine_box(self):
        perf_map = {'LOW': '1', 'MEDIUM': '2', 'HIGH': '3'}
        pot_map = {'LOW': '1', 'MEDIUM': '2', 'HIGH': '3'}
        q = f"{perf_map.get(self.performance_rating, '2')}_{pot_map.get(self.potential_rating, '2')}"
        self.nine_box_quadrant = q
        return q

    def save(self, *args, **kwargs):
        self.calculate_nine_box()
        super().save(*args, **kwargs)


class SuccessionPlan(models.Model):
    READINESS_CHOICES = [
        ('READY_NOW', 'Ready Now (< 3 Months)'),
        ('READY_1_YEAR', 'Ready in 1 Year'),
        ('READY_2_3_YEARS', 'Ready in 2-3 Years'),
        ('EMERGENCY_BACKUP', 'Emergency Contingency Cover'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active Candidate Nomination'),
        ('PROMOTED', 'Promoted into Role'),
        ('ARCHIVED', 'Archived / Reassigned'),
    ]

    critical_position = models.ForeignKey(CriticalRolePosition, on_delete=models.CASCADE, related_name='succession_candidates')
    successor_employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='succession_nominations')
    readiness_level = models.CharField(max_length=25, choices=READINESS_CHOICES, default='READY_1_YEAR')
    ranking_priority = models.PositiveIntegerField(default=1)
    development_needs = models.TextField(blank=True, help_text="Executive mentorship, rotational assignments, technical certifications")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('critical_position', 'successor_employee')
        ordering = ['critical_position', 'ranking_priority']
        verbose_name = 'Succession Candidate Plan'
        verbose_name_plural = 'Succession Candidate Plans'

    def __str__(self):
        return f"{self.successor_employee} -> {self.critical_position.title} ({self.get_readiness_level_display()})"
