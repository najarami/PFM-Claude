"""Parser for Bank of America CSV export format.

BofA exports include metadata rows at the top before the actual headers.
Headers (after skipping metadata): Date,Description,Amount,Running Bal.

Amount: negative = expense, positive = income (credit).
"""
import csv
import io

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction

_HEADER_KEYS = {"Date", "Description", "Amount"}
_BOFA_MARKERS = {"BANK OF AMERICA", "BOFA", "BANKOFAMERICA"}


class BankOfAmericaCSVParser(BaseParser):
    bank = BankName.BANK_OF_AMERICA

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        try:
            text = file_content.decode("utf-8")
            upper = text[:600].upper()
            has_marker = any(m in upper for m in _BOFA_MARKERS) or "bofa" in filename.lower()
            has_headers = "Date,Description,Amount" in text
            return has_marker or (has_headers and "Running Bal" in text)
        except Exception:
            return False

    def parse(self, file: io.IOBase, filename: str) -> list[RawTransaction]:
        content = file.read()
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        lines = text.splitlines()

        # Skip metadata rows until we find the header row
        header_idx = None
        for i, line in enumerate(lines):
            if "Date" in line and "Description" in line and "Amount" in line:
                header_idx = i
                break

        if header_idx is None:
            raise ParseError(f"Could not find header row in BofA file: {filename}")

        data_text = "\n".join(lines[header_idx:])
        reader = csv.DictReader(io.StringIO(data_text), delimiter=",")
        transactions = []

        for row in reader:
            row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
            try:
                raw_date = row.get("Date", "")
                if not raw_date:
                    continue

                tx_date = None
                for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
                    try:
                        tx_date = self._normalize_date(raw_date, fmt)
                        break
                    except ValueError:
                        continue
                if tx_date is None:
                    continue

                raw_desc = row.get("Description", "")
                raw_amount = row.get("Amount", "0")
                amount = self._normalize_amount_usd(raw_amount)

                if amount == 0:
                    continue

                tx_type = "income" if amount > 0 else "expense"

                transactions.append(RawTransaction(
                    date=tx_date,
                    description=raw_desc.strip().upper(),
                    raw_description=raw_desc,
                    amount=amount,
                    currency="USD",
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"BofA row error: {row} -> {e}")

        return transactions
