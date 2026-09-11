from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from accounting.models import JournalEntry, JournalItem, Account
from organizations.models import Branch
from .models import LeaseAgreement, TenantRentInvoice, PropertyUnit, MaintenanceWorkOrder

class LeaseManagementService:
    @classmethod
    @transaction.atomic
    def activate_lease(cls, lease):
        lease.status = 'ACTIVE'
        lease.save(update_fields=['status'])
        unit = lease.unit
        unit.occupancy_status = 'LEASED'
        unit.save(update_fields=['occupancy_status'])
        return lease

    @classmethod
    @transaction.atomic
    def terminate_lease(cls, lease):
        lease.status = 'TERMINATED'
        lease.save(update_fields=['status'])
        unit = lease.unit
        unit.occupancy_status = 'VACANT'
        unit.save(update_fields=['occupancy_status'])
        return lease

    @classmethod
    @transaction.atomic
    def generate_monthly_rent_invoice(cls, lease, year=None, month=None):
        now = timezone.now().date()
        if not year: year = now.year
        if not month: month = now.month

        start_date = timezone.datetime(year, month, 1).date()
        # approximate month end
        if month == 12:
            end_date = timezone.datetime(year, month, 31).date()
        else:
            next_m = timezone.datetime(year, month + 1, 1).date()
            end_date = next_m - timezone.timedelta(days=1)

        total = lease.monthly_rent + lease.cam_fee_monthly
        inv_no = f"RENT-{lease.lease_number}-{year}{month:02d}"

        invoice, created = TenantRentInvoice.objects.get_or_create(
            lease=lease,
            period_start=start_date,
            period_end=end_date,
            defaults={
                'invoice_number': inv_no,
                'base_rent': lease.monthly_rent,
                'cam_charges': lease.cam_fee_monthly,
                'utility_charges': Decimal('0.00'),
                'late_fee': Decimal('0.00'),
                'total_amount': total,
                'paid_amount': Decimal('0.00'),
                'balance_amount': total,
                'status': 'PENDING',
                'due_date': timezone.datetime(year, month, lease.payment_due_day).date()
            }
        )
        return invoice


class RentCollectionService:
    @classmethod
    @transaction.atomic
    def record_rent_payment(cls, invoice, amount, reference_no, user=None):
        amount = Decimal(str(amount))
        invoice.paid_amount += amount
        invoice.balance_amount = max(Decimal('0.00'), invoice.total_amount - invoice.paid_amount)
        if invoice.balance_amount == Decimal('0.00'):
            invoice.status = 'PAID'
        else:
            invoice.status = 'PARTIAL'

        invoice.payment_reference = reference_no
        invoice.paid_date = timezone.now()

        # General ledger posting
        ar_account = Account.objects.filter(account_type='ASSET', name__icontains='Receivable').first()
        if not ar_account:
            ar_account = Account.objects.filter(account_type='ASSET').first()
        cash_account = Account.objects.filter(account_type='ASSET', name__icontains='Cash').first()
        if not cash_account:
            cash_account = Account.objects.filter(account_type='ASSET').first()

        if ar_account and cash_account and user:
            entry = JournalEntry.objects.create(
                entry_number=f"JE-PMS-{invoice.invoice_number}",
                date=timezone.now().date(),
                reference=f"Rent: {invoice.invoice_number}",
                narration=f"Lease Rent Collection: Unit {invoice.lease.unit.unit_number} ({invoice.invoice_number})",
                status='POSTED',
                total_debit=amount,
                total_credit=amount,
                created_by=user
            )
            JournalItem.objects.create(journal_entry=entry, account=cash_account, debit=amount, credit=Decimal('0.00'), description="Rent Cash Inflow")
            JournalItem.objects.create(journal_entry=entry, account=ar_account, debit=Decimal('0.00'), credit=amount, description="Tenant Rent Receivable Cleared")
            invoice.journal_entry = entry

        invoice.save()
        return invoice
