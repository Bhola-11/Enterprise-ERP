from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import (
    BankStatement, BankStatementLine, ReconciliationRule,
    ReconciliationSession
)
from .parsers import (
    CSVBankStatementParser, OFXBankStatementParser,
    MT940BankStatementParser, QIFBankStatementParser
)
from accounting.models import JournalItem, JournalEntry, BankAccount, Account
from sales.models import Payment


class FuzzyReconciliationEngine:
    """
    Automated Multi-Pass Bank Reconciliation Engine with fuzzy scoring,
    auto-matching, and automated adjusting journal entries.
    """

    @classmethod
    def import_statement(cls, bank_account, raw_content, statement_format='CSV', user=None):
        parsers = {
            'CSV': CSVBankStatementParser,
            'OFX': OFXBankStatementParser,
            'MT940': MT940BankStatementParser,
            'QIF': QIFBankStatementParser,
        }
        parser_cls = parsers.get(statement_format, CSVBankStatementParser)
        parser = parser_cls()
        parsed_lines = parser.parse(raw_content)

        if not parsed_lines:
            raise ValueError("No transaction lines could be parsed from the uploaded file.")

        dates = [l['transaction_date'] for l in parsed_lines]
        start_date = min(dates)
        end_date = max(dates)

        with transaction.atomic():
            stmt = BankStatement.objects.create(
                bank_account=bank_account,
                statement_format=statement_format,
                start_date=start_date,
                end_date=end_date,
                total_lines_count=len(parsed_lines),
                reconciled_lines_count=0,
                status='IMPORTED',
                imported_by=user
            )

            for item in parsed_lines:
                BankStatementLine.objects.create(
                    statement=stmt,
                    line_number=item['line_number'],
                    transaction_date=item['transaction_date'],
                    value_date=item.get('value_date'),
                    raw_description=item['raw_description'],
                    transaction_type=item['transaction_type'],
                    amount=item['amount'],
                    balance_after=item.get('balance_after'),
                    transaction_reference=item.get('transaction_reference', ''),
                    counterparty_name=item.get('counterparty_name', ''),
                    status='UNMATCHED'
                )

        return stmt

    @classmethod
    @transaction.atomic
    def execute_auto_reconciliation(cls, statement):
        """
        Runs multi-tier rule matching on unmatched statement lines.
        """
        unmatched_lines = statement.lines.filter(status='UNMATCHED')
        gl_account = statement.bank_account.gl_account if hasattr(statement.bank_account, 'gl_account') and statement.bank_account.gl_account else None

        # Fetch candidate journal items
        candidate_items = JournalItem.objects.filter(
            journal_entry__status='POSTED'
        ).select_related('journal_entry', 'account')

        if gl_account:
            candidate_items = candidate_items.filter(account=gl_account)

        reconciled_count = 0

        for line in unmatched_lines:
            match_found = False

            # 1. Match against Payments
            payment_candidates = Payment.objects.filter(
                amount=line.amount,
                payment_date__range=[line.transaction_date - timezone.timedelta(days=3), line.transaction_date + timezone.timedelta(days=3)]
            )
            if line.transaction_reference:
                ref_match = payment_candidates.filter(reference_number__icontains=line.transaction_reference).first()
                if ref_match:
                    line.matched_payment = ref_match
                    line.status = 'AUTO_MATCHED'
                    line.match_confidence_score = 95
                    line.match_rule_applied = "Exact Amount & Payment Reference Match"
                    line.save()
                    reconciled_count += 1
                    continue

            # 2. Match against General Ledger Journal Items
            # For Bank Credit (Inflow) -> Debit in Ledger Bank Asset
            # For Bank Debit (Outflow) -> Credit in Ledger Bank Asset
            target_debit = line.amount if line.transaction_type == 'CREDIT' else Decimal('0.00')
            target_credit = line.amount if line.transaction_type == 'DEBIT' else Decimal('0.00')

            matched_ji = None
            # Pass A: Exact Date & Amount
            matched_ji = candidate_items.filter(
                journal_entry__date=line.transaction_date,
                debit=target_debit,
                credit=target_credit
            ).exclude(reconciled_statement_lines__status__in=['AUTO_MATCHED', 'MANUALLY_MATCHED']).first()

            if matched_ji:
                line.matched_journal_item = matched_ji
                line.status = 'AUTO_MATCHED'
                line.match_confidence_score = 95
                line.match_rule_applied = "Exact Amount & Date Match on GL Ledger"
                line.save()
                reconciled_count += 1
                continue

            # Pass B: Tolerance window +/- 3 days
            matched_ji = candidate_items.filter(
                journal_entry__date__range=[
                    line.transaction_date - timezone.timedelta(days=3),
                    line.transaction_date + timezone.timedelta(days=3)
                ],
                debit=target_debit,
                credit=target_credit
            ).exclude(reconciled_statement_lines__status__in=['AUTO_MATCHED', 'MANUALLY_MATCHED']).first()

            if matched_ji:
                line.matched_journal_item = matched_ji
                line.status = 'AUTO_MATCHED'
                line.match_confidence_score = 80
                line.match_rule_applied = "Date Window (+/- 3 Days) Amount Match"
                line.save()
                reconciled_count += 1
                continue

        # Update statement counts
        statement.reconciled_lines_count = statement.lines.filter(status__in=['AUTO_MATCHED', 'MANUALLY_MATCHED']).count()
        if statement.reconciled_lines_count == statement.total_lines_count and statement.total_lines_count > 0:
            statement.status = 'RECONCILED'
        elif statement.reconciled_lines_count > 0:
            statement.status = 'IN_PROGRESS'
        statement.save()

        return statement

    @classmethod
    @transaction.atomic
    def post_adjustment_entry(cls, line, contra_account, user=None):
        """
        Creates an automated adjusting journal entry for unmatched bank charges,
        wire fees, or interest income.
        """
        bank_gl = line.statement.bank_account.gl_account or Account.objects.filter(account_type='ASSET', name__icontains='Bank').first()
        if not bank_gl or not contra_account:
            raise ValueError("Bank GL or Contra Account not found for adjustment entry.")

        je = JournalEntry.objects.create(
            entry_number=f"JE-ADJ-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            date=line.transaction_date,
            reference=f"Bank Recon: {line.raw_description[:40]}",
            narration=f"Auto Adjustment for Statement Line #{line.line_number}",
            total_debit=line.amount,
            total_credit=line.amount,
            status='POSTED',
            created_by=user
        )

        if line.transaction_type == 'DEBIT':
            # Bank outflow (e.g. Bank Charges Expense)
            # Debit Expense, Credit Bank Asset
            JournalItem.objects.create(
                journal_entry=je,
                account=contra_account,
                debit=line.amount,
                credit=Decimal('0.00'),
                description=line.raw_description
            )
            bank_item = JournalItem.objects.create(
                journal_entry=je,
                account=bank_gl,
                debit=Decimal('0.00'),
                credit=line.amount,
                description=f"Auto Recon Line #{line.line_number}"
            )
        else:
            # Bank inflow (e.g. Interest Income)
            # Debit Bank Asset, Credit Revenue
            bank_item = JournalItem.objects.create(
                journal_entry=je,
                account=bank_gl,
                debit=line.amount,
                credit=Decimal('0.00'),
                description=f"Auto Recon Line #{line.line_number}"
            )
            JournalItem.objects.create(
                journal_entry=je,
                account=contra_account,
                debit=Decimal('0.00'),
                credit=line.amount,
                description=line.raw_description
            )

        line.matched_journal_item = bank_item
        line.status = 'AUTO_MATCHED'
        line.match_confidence_score = 100
        line.match_rule_applied = f"Auto Adjusting Journal Entry #{je.entry_number}"
        line.save()

        # Update statement
        stmt = line.statement
        stmt.reconciled_lines_count = stmt.lines.filter(status__in=['AUTO_MATCHED', 'MANUALLY_MATCHED']).count()
        if stmt.reconciled_lines_count == stmt.total_lines_count:
            stmt.status = 'RECONCILED'
        stmt.save()

        return je
