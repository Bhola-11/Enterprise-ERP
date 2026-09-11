from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Account, JournalEntry, JournalItem
from audit.middleware import log_audit_event

class AccountingService:
    @staticmethod
    @transaction.atomic
    def post_journal_entry(journal_entry, user=None, request=None):
        je = JournalEntry.objects.select_for_update().get(id=journal_entry.id)
        if je.status == 'POSTED':
            raise ValueError("Journal Entry is already posted.")

        items = je.items.select_related('account').all()
        total_dr = sum(itm.debit for itm in items)
        total_cr = sum(itm.credit for itm in items)

        if total_dr != total_cr:
            raise ValueError(f"Cannot post unbalanced Journal Entry! Total Debits (${total_dr:,.2f}) != Total Credits (${total_cr:,.2f})")
        if total_dr <= Decimal('0.00'):
            raise ValueError("Journal Entry must have a non-zero balanced amount.")

        # Update Chart of Accounts balances
        for itm in items:
            acc = itm.account
            # Normal balances: Asset & Expense = Debit increases, Credit decreases
            # Liability, Equity & Revenue = Credit increases, Debit decreases
            if acc.account_type in ['ASSET', 'EXPENSE']:
                acc.balance += (itm.debit - itm.credit)
            else:
                acc.balance += (itm.credit - itm.debit)
            acc.save(update_fields=['balance'])

        je.total_debit = total_dr
        je.total_credit = total_cr
        je.status = 'POSTED'
        je.posted_at = timezone.now()
        je.save(update_fields=['total_debit', 'total_credit', 'status', 'posted_at'])

        log_audit_event(user, 'APPROVE', 'JournalEntry', je.id, str(je), request=request, description=f"Posted balanced Journal Entry #{je.entry_number} for ${total_dr:,.2f}")
        return je

    @staticmethod
    def get_financial_summary():
        assets = sum(a.balance for a in Account.objects.filter(account_type='ASSET', is_active=True))
        liabilities = sum(a.balance for a in Account.objects.filter(account_type='LIABILITY', is_active=True))
        equity = sum(a.balance for a in Account.objects.filter(account_type='EQUITY', is_active=True))
        revenue = sum(a.balance for a in Account.objects.filter(account_type='REVENUE', is_active=True))
        expenses = sum(a.balance for a in Account.objects.filter(account_type='EXPENSE', is_active=True))
        net_profit = revenue - expenses

        return {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'revenue': revenue,
            'expenses': expenses,
            'net_profit': net_profit,
        }
