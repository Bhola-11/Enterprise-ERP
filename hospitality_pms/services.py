from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from accounting.models import JournalEntry, JournalItem, Account
from organizations.models import Branch
from .models import (
    RoomReservation, GuestFolioInvoice, FolioChargeLine,
    HotelRoom, HousekeepingTask
)

class FrontDeskService:
    @classmethod
    @transaction.atomic
    def process_check_in(cls, reservation, room=None):
        if room:
            reservation.room = room
        if not reservation.room:
            raise ValueError("No room assigned for check-in.")

        reservation.status = 'CHECKED_IN'
        reservation.actual_check_in_time = timezone.now()
        reservation.save()

        # Update room status
        reservation.room.status = 'OCCUPIED'
        reservation.room.save(update_fields=['status'])

        # Initialize Guest Folio
        folio, created = GuestFolioInvoice.objects.get_or_create(
            reservation=reservation,
            defaults={
                'folio_number': f"FOL-{reservation.confirmation_code}",
                'guest': reservation.guest,
                'total_room_charges': reservation.total_room_charge,
                'total_incidentals': Decimal('0.00'),
                'tax_charges': (reservation.total_room_charge * Decimal('0.10')).quantize(Decimal('0.01')),
                'total_amount': reservation.total_room_charge * Decimal('1.10'),
                'paid_amount': reservation.deposit_paid,
                'balance_amount': (reservation.total_room_charge * Decimal('1.10')) - reservation.deposit_paid,
                'status': 'OPEN'
            }
        )

        # Add initial room charge line
        if created:
            FolioChargeLine.objects.create(
                folio=folio,
                charge_type='ROOM_NIGHT',
                description=f"Accommodation: {reservation.total_nights} nights @ ${reservation.nightly_rate}/night",
                amount=reservation.total_room_charge
            )
            FolioChargeLine.objects.create(
                folio=folio,
                charge_type='RESORT_FEE',
                description="City Tourism Tax & Amenity Surcharge (10%)",
                amount=(reservation.total_room_charge * Decimal('0.10')).quantize(Decimal('0.01'))
            )
        return folio

    @classmethod
    @transaction.atomic
    def process_check_out(cls, reservation, payment_amount=None, user=None):
        reservation.status = 'CHECKED_OUT'
        reservation.actual_check_out_time = timezone.now()
        reservation.save()

        room = reservation.room
        if room:
            room.status = 'CLEANING'
            room.save(update_fields=['status'])

            # Automatically dispatch Housekeeping task
            HousekeepingTask.objects.create(
                room=room,
                task_type='CHECKOUT_DEEP_CLEAN',
                status='PENDING',
                notes=f"Departure clean for {reservation.guest.full_name}."
            )

        # Settle Folio
        folio = getattr(reservation, 'folio', None)
        if folio:
            if payment_amount is None:
                payment_amount = folio.balance_amount
            folio.paid_amount += Decimal(str(payment_amount))
            folio.balance_amount = max(Decimal('0.00'), folio.total_amount - folio.paid_amount)
            if folio.balance_amount == Decimal('0.00'):
                folio.status = 'SETTLED'
                folio.settled_at = timezone.now()

            # Post to General Ledger
            ar_account = Account.objects.filter(account_type='ASSET', name__icontains='Receivable').first()
            if not ar_account:
                ar_account = Account.objects.filter(account_type='ASSET').first()
            cash_account = Account.objects.filter(account_type='ASSET', name__icontains='Cash').first()
            if not cash_account:
                cash_account = Account.objects.filter(account_type='ASSET').first()

            if ar_account and cash_account and user and payment_amount > 0:
                entry = JournalEntry.objects.create(
                    entry_number=f"JE-HTL-{folio.folio_number}",
                    date=timezone.now().date(),
                    reference=f"Folio: {folio.folio_number}",
                    narration=f"Guest Folio Settlement: {folio.folio_number} - {reservation.guest.full_name}",
                    status='POSTED',
                    total_debit=payment_amount,
                    total_credit=payment_amount,
                    created_by=user
                )
                JournalItem.objects.create(journal_entry=entry, account=cash_account, debit=payment_amount, credit=Decimal('0.00'), description="Front Desk Folio Settlement")
                JournalItem.objects.create(journal_entry=entry, account=ar_account, debit=Decimal('0.00'), credit=payment_amount, description="Guest Ledger Cleared")
                folio.journal_entry = entry

            folio.save()
        return reservation


class FolioBillingService:
    @classmethod
    @transaction.atomic
    def post_charge(cls, folio, charge_type, description, amount):
        amount = Decimal(str(amount))
        line = FolioChargeLine.objects.create(
            folio=folio,
            charge_type=charge_type,
            description=description,
            amount=amount
        )
        folio.total_incidentals += amount
        folio.total_amount += amount
        folio.balance_amount += amount
        folio.save()
        return line
