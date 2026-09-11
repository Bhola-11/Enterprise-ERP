from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounting.models import BankAccount, Account, JournalEntry, JournalItem
from reconciliation.models import BankStatement, BankStatementLine, ReconciliationRule
from reconciliation.parsers import (
    CSVBankStatementParser, OFXBankStatementParser,
    MT940BankStatementParser, QIFBankStatementParser
)
from reconciliation.services import FuzzyReconciliationEngine

User = get_user_model()


class ReconciliationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="auditor", email="auditor@nexora.io", password="Password@123", role="ADMIN")

        self.bank_gl = Account.objects.create(
            name="Main Operating Bank Account",
            code="1010",
            account_type="ASSET"
        )

        self.expense_gl = Account.objects.create(
            name="Bank Service Charges",
            code="5050",
            account_type="EXPENSE"
        )

        self.bank_account = BankAccount.objects.create(
            bank_name="Chase Commercial Banking",
            account_number="CHK-987654321",
            currency="USD",
            gl_account=self.bank_gl
        )

    def test_csv_parser(self):
        csv_data = """Date,Description,Debit,Credit,Balance,Reference
2026-09-01,Customer Wire Deposit,,5000.00,15000.00,CUST-WIRE-101
2026-09-02,Vendor Payment Outflow,1200.00,,13800.00,VEND-PAY-202
2026-09-03,Monthly Maintenance Fee,25.00,,13775.00,FEE-SEP
"""
        parser = CSVBankStatementParser()
        lines = parser.parse(csv_data)
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0]['transaction_type'], 'CREDIT')
        self.assertEqual(lines[0]['amount'], Decimal('5000.00'))
        self.assertEqual(lines[1]['transaction_type'], 'DEBIT')
        self.assertEqual(lines[1]['amount'], Decimal('1200.00'))

    def test_ofx_parser(self):
        ofx_data = """
<OFX>
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20260905120000
<TRNAMT>2500.00
<FITID>OFX123456
<NAME>Acme Corp Payment
<MEMO>Invoice Settlement
</STMTTRN>
</BANKTRANLIST>
</OFX>
"""
        parser = OFXBankStatementParser()
        lines = parser.parse(ofx_data)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['amount'], Decimal('2500.00'))
        self.assertEqual(lines[0]['transaction_type'], 'CREDIT')
        self.assertEqual(lines[0]['transaction_reference'], 'OFX123456')

    def test_qif_parser(self):
        qif_data = """!Type:Bank
D05/09/2026
T-75.00
PWire Transfer Fee
MService Charge
^
"""
        parser = QIFBankStatementParser()
        lines = parser.parse(qif_data)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['amount'], Decimal('75.00'))
        self.assertEqual(lines[0]['transaction_type'], 'DEBIT')

    def test_auto_reconciliation_and_adjustment_posting(self):
        # 1. Post a Journal Entry in GL
        je = JournalEntry.objects.create(
            entry_number="JE-TEST-001",
            date=timezone.now().date(),
            reference="CUST-WIRE-101",
            narration="Client invoice settlement",
            total_debit=Decimal('5000.00'),
            total_credit=Decimal('5000.00'),
            status="POSTED"
        )
        ji_bank = JournalItem.objects.create(
            journal_entry=je,
            account=self.bank_gl,
            debit=Decimal('5000.00'),
            credit=Decimal('0.00'),
            description="Bank deposit"
        )

        # 2. Import Statement
        csv_data = f"""Date,Description,Debit,Credit,Balance,Reference
{timezone.now().strftime('%Y-%m-%d')},Customer Deposit,,5000.00,5000.00,CUST-WIRE-101
{timezone.now().strftime('%Y-%m-%d')},Bank Service Fee,25.00,,4975.00,FEE-01
"""
        stmt = FuzzyReconciliationEngine.import_statement(
            bank_account=self.bank_account,
            raw_content=csv_data,
            statement_format='CSV',
            user=self.user
        )
        self.assertEqual(stmt.total_lines_count, 2)

        # 3. Run Auto-Reconciliation
        FuzzyReconciliationEngine.execute_auto_reconciliation(stmt)
        stmt.refresh_from_db()
        self.assertEqual(stmt.reconciled_lines_count, 1)

        # Line 1 should be matched with ji_bank
        line1 = stmt.lines.get(line_number=1)
        self.assertEqual(line1.status, 'AUTO_MATCHED')
        self.assertEqual(line1.matched_journal_item, ji_bank)

        # 4. Post adjustment for Line 2 (Fee)
        line2 = stmt.lines.get(line_number=2)
        self.assertEqual(line2.status, 'UNMATCHED')

        adj_je = FuzzyReconciliationEngine.post_adjustment_entry(line2, self.expense_gl, user=self.user)
        self.assertTrue(adj_je.entry_number.startswith("JE-ADJ-"))

        stmt.refresh_from_db()
        self.assertEqual(stmt.status, 'RECONCILED')
        self.assertEqual(stmt.reconciled_lines_count, 2)
