from decimal import Decimal
from django.db.models import Avg, Count
from django.utils import timezone
from .models import AppraisalSubmission, AppraisalCycle

class AppraisalScoringEngine:
    @classmethod
    def calculate_composite_score(cls, submission):
        """
        Calculates 360-degree weighted composite score:
        - Self Rating: 15%
        - Peer Average: 25%
        - Manager Evaluation: 60%
        """
        self_wt = Decimal('0.15')
        peer_wt = Decimal('0.25')
        mgr_wt = Decimal('0.60')

        s_score = submission.self_rating or Decimal('3.00')
        p_score = submission.peer_average_rating or Decimal('3.00')
        m_score = submission.manager_rating or Decimal('3.00')

        composite = (s_score * self_wt) + (p_score * peer_wt) + (m_score * mgr_wt)
        composite = composite.quantize(Decimal('0.01'))

        # Assign Band
        if composite >= Decimal('4.50'):
            band = 'OUTSTANDING'
        elif composite >= Decimal('3.75'):
            band = 'EXCEEDS'
        elif composite >= Decimal('2.75'):
            band = 'MEETS'
        elif composite >= Decimal('2.00'):
            band = 'NEEDS_IMPROVEMENT'
        else:
            band = 'UNSATISFACTORY'

        submission.calibrated_final_score = composite
        submission.overall_band = band
        if submission.manager_summary and submission.self_summary:
            submission.status = 'COMPLETED'
            submission.completed_at = timezone.now()
        submission.save(update_fields=['calibrated_final_score', 'overall_band', 'status', 'completed_at'])
        return composite, band

    @classmethod
    def get_cycle_analytics(cls, cycle):
        submissions = cycle.submissions.all()
        total = submissions.count()
        completed = submissions.filter(status='COMPLETED').count()

        avg_score = submissions.filter(status='COMPLETED').aggregate(a=Avg('calibrated_final_score'))['a'] or Decimal('0.00')

        band_distribution = {
            'OUTSTANDING': submissions.filter(overall_band='OUTSTANDING', status='COMPLETED').count(),
            'EXCEEDS': submissions.filter(overall_band='EXCEEDS', status='COMPLETED').count(),
            'MEETS': submissions.filter(overall_band='MEETS', status='COMPLETED').count(),
            'NEEDS_IMPROVEMENT': submissions.filter(overall_band='NEEDS_IMPROVEMENT', status='COMPLETED').count(),
            'UNSATISFACTORY': submissions.filter(overall_band='UNSATISFACTORY', status='COMPLETED').count(),
        }

        completion_rate = (completed / total * 100) if total > 0 else 0

        return {
            'total_submissions': total,
            'completed_count': completed,
            'completion_rate': round(completion_rate, 1),
            'average_score': round(avg_score, 2),
            'band_distribution': band_distribution
        }
