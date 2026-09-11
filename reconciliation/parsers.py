import csv
import io
import re
from datetime import datetime
from decimal import Decimal
import xml.etree.ElementTree as ET


class BaseStatementParser:
    """Base parser interface for electronic bank statement files."""
    def parse(self, file_content):
        raise NotImplementedError("Subclasses must implement parse()")


class CSVBankStatementParser(BaseStatementParser):
    """
    Parses CSV bank files with flexible column headers:
    Date, Description / Narrative, Debit, Credit, Balance, Ref
    """

    def parse(self, file_content):
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8', errors='ignore')

        reader = csv.DictReader(io.StringIO(file_content))
        lines = []
        line_num = 1

        for row in reader:
            normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            # Extract date
            raw_date = normalized.get('date') or normalized.get('txn_date') or normalized.get('transaction date') or normalized.get('value date')
            if not raw_date:
                continue

            parsed_date = None
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y%m%d'):
                try:
                    parsed_date = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    pass

            if not parsed_date:
                parsed_date = datetime.now().date()

            desc = normalized.get('description') or normalized.get('narration') or normalized.get('details') or normalized.get('memo') or 'Bank Transaction'
            ref = normalized.get('reference') or normalized.get('ref') or normalized.get('cheque no') or normalized.get('chq no') or ''
            counterparty = normalized.get('counterparty') or normalized.get('party') or normalized.get('payee') or ''

            debit = Decimal(str(normalized.get('debit', '0') or '0').replace('$', '').replace(',', ''))
            credit = Decimal(str(normalized.get('credit', '0') or '0').replace('$', '').replace(',', ''))
            amount_val = normalized.get('amount') or normalized.get('txn amount')

            if amount_val and debit == Decimal('0.00') and credit == Decimal('0.00'):
                clean_amt = Decimal(str(amount_val).replace('$', '').replace(',', ''))
                if clean_amt < 0:
                    txn_type = 'DEBIT'
                    amount = abs(clean_amt)
                else:
                    txn_type = 'CREDIT'
                    amount = clean_amt
            elif debit > Decimal('0.00'):
                txn_type = 'DEBIT'
                amount = debit
            else:
                txn_type = 'CREDIT'
                amount = credit

            bal = normalized.get('balance') or normalized.get('closing balance')
            balance_after = Decimal(str(bal).replace('$', '').replace(',', '')) if bal else None

            lines.append({
                'line_number': line_num,
                'transaction_date': parsed_date,
                'value_date': parsed_date,
                'raw_description': desc,
                'transaction_type': txn_type,
                'amount': amount,
                'balance_after': balance_after,
                'transaction_reference': ref,
                'counterparty_name': counterparty
            })
            line_num += 1

        return lines


class OFXBankStatementParser(BaseStatementParser):
    """
    Parses Open Financial Exchange (OFX) statement files.
    """

    def parse(self, file_content):
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8', errors='ignore')

        lines = []
        line_num = 1

        # Extract transaction blocks: <STMTTRN>...</STMTTRN>
        trn_pattern = re.compile(r'<STMTTRN>(.*?)</STMTTRN>', re.DOTALL | re.IGNORECASE)
        transactions = trn_pattern.findall(file_content)

        for trn in transactions:
            # Type: <TRNTYPE>DEBIT/CREDIT
            ttype_m = re.search(r'<TRNTYPE>([^<\r\n]+)', trn, re.IGNORECASE)
            ttype = ttype_m.group(1).strip().upper() if ttype_m else 'CREDIT'

            # Date: <DTPOSTED>20260901...
            dt_m = re.search(r'<DTPOSTED>([0-9]{8})', trn, re.IGNORECASE)
            parsed_date = datetime.strptime(dt_m.group(1), '%Y%m%d').date() if dt_m else datetime.now().date()

            # Amount: <TRNAMT>-120.50
            amt_m = re.search(r'<TRNAMT>([^<\r\n]+)', trn, re.IGNORECASE)
            raw_amt = Decimal(amt_m.group(1).strip()) if amt_m else Decimal('0.00')

            txn_type = 'DEBIT' if raw_amt < 0 or ttype in ['DEBIT', 'CHECK', 'PAYMENT', 'FEE'] else 'CREDIT'
            amount = abs(raw_amt)

            # Ref: <FITID> or <CHECKNUM>
            fitid_m = re.search(r'<FITID>([^<\r\n]+)', trn, re.IGNORECASE)
            ref = fitid_m.group(1).strip() if fitid_m else ''

            # Name / Payee: <NAME>
            name_m = re.search(r'<NAME>([^<\r\n]+)', trn, re.IGNORECASE)
            counterparty = name_m.group(1).strip() if name_m else ''

            # Memo: <MEMO>
            memo_m = re.search(r'<MEMO>([^<\r\n]+)', trn, re.IGNORECASE)
            memo = memo_m.group(1).strip() if memo_m else counterparty or 'OFX Bank Transfer'

            lines.append({
                'line_number': line_num,
                'transaction_date': parsed_date,
                'value_date': parsed_date,
                'raw_description': f"{counterparty} - {memo}".strip(' -'),
                'transaction_type': txn_type,
                'amount': amount,
                'balance_after': None,
                'transaction_reference': ref,
                'counterparty_name': counterparty
            })
            line_num += 1

        return lines


class MT940BankStatementParser(BaseStatementParser):
    """
    Parses SWIFT MT940 electronic statements (:61: Statement Line, :86: Information to Account Owner).
    """

    def parse(self, file_content):
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8', errors='ignore')

        lines = []
        line_num = 1

        # Match :61: statement lines
        # Pattern: :61:YYMMDD(MMDD)?(C|D|RC|RD)Amount(N|F)?...
        raw_lines = file_content.splitlines()
        current_61 = None
        current_86 = ""

        for l in raw_lines:
            if l.startswith(':61:'):
                if current_61:
                    lines.append(self._process_mt940_entry(line_num, current_61, current_86))
                    line_num += 1
                current_61 = l[4:].strip()
                current_86 = ""
            elif l.startswith(':86:'):
                current_86 = l[4:].strip()
            elif current_86 and not l.startswith(':'):
                current_86 += " " + l.strip()

        if current_61:
            lines.append(self._process_mt940_entry(line_num, current_61, current_86))

        return lines

    def _process_mt940_entry(self, line_num, field61, field86):
        date_str = field61[:6]
        parsed_date = datetime.strptime(date_str, '%y%m%d').date()

        # Check Credit or Debit
        rest = field61[6:]
        if rest.startswith('C') or rest.startswith('RC'):
            txn_type = 'CREDIT'
            rest = rest[1:] if rest.startswith('C') else rest[2:]
        else:
            txn_type = 'DEBIT'
            rest = rest[1:] if rest.startswith('D') else rest[2:]

        # Extract amount
        amt_match = re.match(r'([0-9,]+)', rest)
        amount_str = amt_match.group(1).replace(',', '.') if amt_match else '0.00'
        amount = Decimal(amount_str)

        return {
            'line_number': line_num,
            'transaction_date': parsed_date,
            'value_date': parsed_date,
            'raw_description': field86 or 'SWIFT MT940 Wire Transfer',
            'transaction_type': txn_type,
            'amount': amount,
            'balance_after': None,
            'transaction_reference': field86[:30] if field86 else f"MT940-{line_num}",
            'counterparty_name': ''
        }


class QIFBankStatementParser(BaseStatementParser):
    """
    Parses Quicken Interchange Format (QIF) files.
    """

    def parse(self, file_content):
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8', errors='ignore')

        lines = []
        line_num = 1

        entries = file_content.split('^')
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue

            parsed_date = datetime.now().date()
            amount = Decimal('0.00')
            payee = ''
            memo = ''
            ref = ''
            has_amount = False

            for row in entry.splitlines():
                row = row.strip()
                if not row or row.startswith('!'):
                    continue
                code = row[0]
                val = row[1:].strip()

                if code == 'D':
                    for fmt in ('%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d/%m/%y', '%m/%d/%y'):
                        try:
                            parsed_date = datetime.strptime(val, fmt).date()
                            break
                        except ValueError:
                            pass
                elif code == 'T':
                    clean_val = val.replace('$', '').replace(',', '')
                    raw_amt = Decimal(clean_val)
                    txn_type = 'DEBIT' if raw_amt < 0 else 'CREDIT'
                    amount = abs(raw_amt)
                elif code == 'P':
                    payee = val
                elif code == 'M':
                    memo = val
                elif code == 'N':
                    ref = val

            lines.append({
                'line_number': line_num,
                'transaction_date': parsed_date,
                'value_date': parsed_date,
                'raw_description': f"{payee} {memo}".strip() or 'QIF Bank Record',
                'transaction_type': txn_type,
                'amount': amount,
                'balance_after': None,
                'transaction_reference': ref,
                'counterparty_name': payee
            })
            line_num += 1

        return lines
