"""Parser for Wells Fargo CSV export format.

Wells Fargo exports have NO header row. 5 columns in order:
  date (MM/DD/YYYY), amount, *, *, description

Amount: negative = expense, positive = income.
Detection relies on filename containing 'wellsfargo' or 'wells_fargo'.
"""
import csv
import io
from decimal import Decimal

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction


class WellsFargoCSVParser(BaseParser):
    bank = BankName.WELLS_FARGO

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        lower_name = filename.lower()
        if "wellsfargo" in lower_name or "wells_fargo" in lower_name or "wells fargo" in lower_name:
            return True
        try:
            text = file_content.decode("utf-8")
            return "WELLS FARGO" in text[:400].upper()
        except Exception:
            return False

    def parse(self, file: io.IOBase, filename: str) -> list[RawTransaction]:
        content = file.read()
        text = content.decode("utf-8") if isinstance(content, bytes) else content

        # Wells Fargo has no headers — read as raw rows
        reader = csv.reader(io.StringIO(text), delimiter=",")
        transactions = []

        for row in reader:
            if len(row) < 5:
                continue
            try:
                raw_date = row[0].strip()
                raw_amount = row[1].strip()
                raw_desc = row[4].strip()   # 5th column is description

                if not raw_date or not raw_amount:
                    continue

                # Skip if date doesn't look like MM/DD/YYYY
                if not raw_date.count("/") == 2:
                    continue

                tx_date = None
                for fmt in ("%m/%d/%Y", "%m/%d/%y"):
                    try:
                        tx_date = self._normalize_date(raw_date, fmt)
                        break
                    except ValueError:
                        continue
                if tx_date is None:
                    continue

                amount = self._normalize_amount_usd(raw_amount)
                if amount == Decimal("0"):
                    continue

                tx_type = "income" if amount > 0 else "expense"

                transactions.append(RawTransaction(
                    date=tx_date,
                    description=raw_desc.upper(),
                    raw_description=raw_desc,
                    amount=amount,
                    currency="USD",
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"Wells Fargo row error: {row} -> {e}")

        return transactions
