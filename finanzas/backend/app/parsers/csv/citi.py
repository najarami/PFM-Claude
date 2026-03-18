"""Parser for Citi CSV export format.

Headers: Status,Date,Description,Debit,Credit

Debit = expense (money out), Credit = income/payment (money in).
Amounts are positive values in their respective column.
"""
import csv
import io
from decimal import Decimal

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction

_HEADER_KEYS = {"Status", "Date", "Description", "Debit", "Credit"}
_CITI_MARKERS = {"CITIBANK", "CITI ", "CITI,"}


class CitiCSVParser(BaseParser):
    bank = BankName.CITI

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        lower_name = filename.lower()
        if "citi" in lower_name:
            return True
        try:
            text = file_content.decode("utf-8")
            first_line = text.splitlines()[0] if text.strip() else ""
            cols = {c.strip() for c in first_line.split(",")}
            has_headers = _HEADER_KEYS.issubset(cols)
            upper = text[:400].upper()
            has_marker = any(m in upper for m in _CITI_MARKERS)
            return has_headers or (has_headers and has_marker)
        except Exception:
            return False

    def parse(self, file: io.IOBase, filename: str) -> list[RawTransaction]:
        content = file.read()
        text = content.decode("utf-8") if isinstance(content, bytes) else content

        reader = csv.DictReader(io.StringIO(text), delimiter=",")
        transactions = []

        for row in reader:
            row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
            try:
                status = row.get("Status", "").upper()
                if status in ("PENDING", ""):
                    pass  # include pending transactions

                raw_date = row.get("Date", "")
                if not raw_date:
                    continue

                tx_date = None
                for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
                    try:
                        tx_date = self._normalize_date(raw_date, fmt)
                        break
                    except ValueError:
                        continue
                if tx_date is None:
                    continue

                raw_desc = row.get("Description", "")
                debit = row.get("Debit", "").strip()
                credit = row.get("Credit", "").strip()

                if debit and debit not in ("", "0", "0.00"):
                    amount = -self._normalize_amount_usd(debit)
                    tx_type = "expense"
                elif credit and credit not in ("", "0", "0.00"):
                    amount = self._normalize_amount_usd(credit)
                    tx_type = "income"
                else:
                    continue

                if amount == Decimal("0"):
                    continue

                transactions.append(RawTransaction(
                    date=tx_date,
                    description=raw_desc.strip().upper(),
                    raw_description=raw_desc.strip(),
                    amount=amount,
                    currency="USD",
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"Citi row error: {row} -> {e}")

        return transactions
