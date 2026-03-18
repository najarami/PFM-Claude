"""Parser for American Express CSV export format.

Headers: Date,Description,Amount  (or Date,Description,Card Member,Account #,Amount)

IMPORTANT: Amex exports use POSITIVE amounts for charges (expenses) and NEGATIVE for credits.
This is the inverse of the sign convention used elsewhere in the app.
"""
import csv
import io

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction

_AMEX_MARKERS = {"AMERICAN EXPRESS", "AMERICANEXPRESS", "AMEX"}


class AmexCSVParser(BaseParser):
    bank = BankName.AMEX

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        lower_name = filename.lower()
        if "amex" in lower_name or "american_express" in lower_name or "americanexpress" in lower_name:
            return True
        try:
            text = file_content.decode("utf-8")
            upper = text[:600].upper()
            first_line = text.splitlines()[0] if text.strip() else ""
            has_marker = any(m in upper for m in _AMEX_MARKERS)
            has_header = "Date" in first_line and "Description" in first_line and "Amount" in first_line
            return has_marker and has_header
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
                raw_date = row.get("Date", "")
                if not raw_date:
                    continue

                tx_date = None
                for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
                    try:
                        tx_date = self._normalize_date(raw_date, fmt)
                        break
                    except ValueError:
                        continue
                if tx_date is None:
                    continue

                raw_desc = row.get("Description", "")
                raw_amount = row.get("Amount", "0")

                # Amex: positive = charge (expense), negative = payment/credit (income)
                amount_raw = self._normalize_amount_usd(raw_amount)

                if amount_raw == 0:
                    continue

                if amount_raw > 0:
                    # Positive = charge = expense → store as negative
                    amount = -amount_raw
                    tx_type = "expense"
                else:
                    # Negative = credit/payment = income → store as positive
                    amount = abs(amount_raw)
                    tx_type = "income"

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
                raise ParseError(f"Amex row error: {row} -> {e}")

        return transactions
