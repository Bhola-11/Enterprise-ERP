from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import QualityInspectionTicket, NonConformanceReport, CAPAAction

class SamplingEngine:
    """
    ISO 2859-1 / ANSI ASQ Z1.4 Normal Sampling Table Calculator
    """
    @classmethod
    def compute_sample_size(cls, lot_size, standard='AQL_2_5'):
        if standard == 'FULL_100':
            return lot_size
        lot = int(lot_size)
        if lot <= 8: return min(lot, 2)
        if lot <= 15: return min(lot, 3)
        if lot <= 25: return min(lot, 5)
        if lot <= 50: return min(lot, 8)
        if lot <= 90: return min(lot, 13)
        if lot <= 150: return min(lot, 20)
        if lot <= 280: return min(lot, 32)
        if lot <= 500: return min(lot, 50)
        if lot <= 1200: return min(lot, 80)
        if lot <= 3200: return min(lot, 125)
        return min(lot, 200)


class QualityDispositionService:
    @classmethod
    @transaction.atomic
    def record_inspection_verdict(cls, ticket, accepted_qty, rejected_qty, notes="", user=None):
        ticket.accepted_quantity = accepted_qty
        ticket.rejected_quantity = rejected_qty
        ticket.inspected_quantity = accepted_qty + rejected_qty
        ticket.inspector = user
        ticket.inspector_notes = notes

        if rejected_qty > 0:
            ticket.disposition = 'REJECTED'
            # Automatically spawn an NCR
            ncr_no = f"NCR-{ticket.ticket_number}-{timezone.now().strftime('%m%d%H%M')}"
            ncr = NonConformanceReport.objects.create(
                ncr_number=ncr_no,
                ticket=ticket,
                defect_title=f"Sample inspection failure on {ticket.reference_code}",
                defect_severity='MAJOR',
                defect_description=f"Rejected {rejected_qty} units out of sample size {ticket.sample_size}. {notes}",
                containment_action="Lot placed in Quarantine Hold. Supplier/Shop floor notified.",
                status='OPEN',
                reported_by=user
            )
        else:
            ticket.disposition = 'ACCEPTED'

        ticket.status = 'COMPLETED'
        ticket.save()
        return ticket
