from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from hr.models import Employee, Department

class AppraisalCycle(models.Model):
    CYCLE_TYPES = [
        ('ANNUAL', 'Annual Performance & Compensation Review'),
        ('MID_YEAR', 'Mid-Year Milestone Check-in'),
        ('QUARTERLY', 'Quarterly OKR & Goal Review'),
        ('PROBATION', '90-Day Probationary Evaluation'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Draft / Setup'),
        ('ACTIVE', 'Active in Review Process'),
        ('IN_CALIBRATION', 'Under Executive Calibration'),
        ('CLOSED', 'Cycle Finalized & Closed'),
    ]

    name = models.CharField(max_length=150)
    cycle_type = models.CharField(max_length=20, choices=CYCLE_TYPES, default='ANNUAL')
    start_date = models.DateField()
    end_date = models.DateField()
    self_review_deadline = models.DateField()
    manager_review_deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Appraisal Cycle'
        verbose_name_plural = 'Appraisal Cycles'

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def total_submissions(self):
        return self.submissions.count()

    @property
    def completed_count(self):
        return self.submissions.filter(status='COMPLETED').count()


class CompetencyFramework(models.Model):
    CATEGORIES = [
        ('CORE_VALUE', 'Core Organizational Values & Ethics'),
        ('FUNCTIONAL_EXPERTISE', 'Functional / Technical Domain Excellence'),
        ('LEADERSHIP_MANAGEMENT', 'Leadership, Coaching & Strategic Vision'),
        ('INNOVATION_AGILITY', 'Innovation, Agility & Continuous Learning'),
    ]

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=CATEGORIES, default='CORE_VALUE')
    description = models.TextField(help_text="Behavioral indicators and measurement criteria")
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('25.00'))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Competency Framework'
        verbose_name_plural = 'Competency Frameworks'

    def __str__(self):
        return f"{self.name} ({self.get_category_display()} - {self.weight_percentage}%)"


class AppraisalSubmission(models.Model):
    OVERALL_BANDS = [
        ('OUTSTANDING', '5 - Top Tier / Outstanding (Top 10%)'),
        ('EXCEEDS', '4 - Exceeds Expectations'),
        ('MEETS', '3 - Consistently Meets Expectations'),
        ('NEEDS_IMPROVEMENT', '2 - Needs Improvement / Development Plan'),
        ('UNSATISFACTORY', '1 - Unsatisfactory Performance'),
    ]
    STATUS_CHOICES = [
        ('PENDING_SELF', 'Pending Self Review'),
        ('PENDING_MANAGER', 'Pending Manager Review'),
        ('IN_CALIBRATION', 'Under Calibration Committee'),
        ('COMPLETED', 'Completed & Signed Off'),
    ]

    cycle = models.ForeignKey(AppraisalCycle, on_delete=models.CASCADE, related_name='submissions')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='appraisal_submissions')
    manager = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='evaluated_appraisals')

    self_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('3.00'))
    self_summary = models.TextField(blank=True, help_text="Major accomplishments, OKR achievements, and learnings")

    peer_average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('3.00'))
    
    manager_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('3.00'))
    manager_summary = models.TextField(blank=True, help_text="Executive review, strengths, growth areas, promotion readiness")

    calibrated_final_score = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('3.00'))
    overall_band = models.CharField(max_length=25, choices=OVERALL_BANDS, default='MEETS')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_SELF')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('cycle', 'employee')
        ordering = ['-cycle', 'employee']
        verbose_name = 'Appraisal Submission'
        verbose_name_plural = 'Appraisal Submissions'

    def __str__(self):
        return f"{self.cycle.name} - {self.employee}: Score {self.calibrated_final_score} ({self.get_overall_band_display()})"


class ContinuousFeedbackNote(models.Model):
    FEEDBACK_TYPES = [
        ('PRAISE', 'Kudos / Public Peer Praise'),
        ('CONSTRUCTIVE', 'Constructive Coaching Observation'),
        ('CHECK_IN_NOTE', '1-on-1 Check-in Summary'),
        ('GOAL_MILESTONE', 'Goal / OKR Milestone Achieved'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='received_feedbacks')
    giver = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='given_feedbacks')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, default='PRAISE')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_private_manager = models.BooleanField(default=False, help_text="Visible only to employee managers and HR")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Continuous Feedback & 1-on-1 Note'
        verbose_name_plural = 'Continuous Feedback & 1-on-1 Notes'

    def __str__(self):
        return f"{self.get_feedback_type_display()} for {self.employee} from {self.giver}"
