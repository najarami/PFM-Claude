"""Parser for Charles Schwab CSV export format.

Schwab includes metadata/summary rows at the top. Data rows follow after
a header line containing "Date,Action,...".

Headers: Date,Action,Symbol,Description,Quantity,Price,Fees & Comm,Amount

Amount: negative = expense (bought, wire out), positive = income (dividends, interest, wire in).
"""
import csv
import io
from decimal import Decimal

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction

_SCHWAB_MARKERS = {"SCHWAB", "CHARLES SCHWAB"}

# Actions that represent income
_INCOME_ACTIONS = {
    "BANK INTEREST", "DIVIDEND", "QUALIFIED DIVIDEND", "NON-QUALIFIED DIV",
    "JOURNALED SHARES", "WIRE FUNDS RECEIVED", "CASH DIVIDENDS",
    "SPECIAL QUAL DIV", "MONEYLINK TRANSFER",
}
# Actions that represent expenses
_EXPENSE_ACTIONS = {
    "BUY", "BOUGHT", "WIRE FUNDS SENT", "ADVISORY FEE", "MARGIN INTEREST",
    "SELL SHORT",
}
_TRANSFER_ACTIONS = {"JOURNALED SHARES", "INTERNAL TRANSFER"}


class SchwabCSVParser(BaseParser):
    bank = BankName.SCHWAB

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        lower_name = filename.lower()
        if "schwab" in lower_name:
            return True
        try:
            text = file_content.decode("utf-8")
            upper = text[:500].upper()
            return any(m in upper for m in _SCHWAB_MARKERS)
        except Exception:
            return False

    def parse(self, file: io.IOBase, filename: str) -> list[RawTransaction]:
        content = file.read()
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        lines = text.splitlines()

        # Find header line
        header_idx = None
        for i, line in enumerate(lines):
            if "Date" in line and "Action" in line and "Amount" in line:
                header_idx = i
                break

        if header_idx is None:
            raise ParseError(f"Could not find header row in Schwab file: {filename}")

        data_text = "\n".join(lines[header_idx:])
        reader = csv.DictReader(io.StringIO(data_text), delimiter=",")
        transactions = []

        for row in reader:
            row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
            try:
                raw_date = row.get("Date", "")
                if not raw_date or raw_date.startswith("Total") or not row.get("Action"):
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

                raw_amount = row.get("Amount", "0")
                if not raw_amount or raw_amount in ("--", ""):
                    continue

                amount = self._normalize_amount_usd(raw_amount)
                if amount == Decimal("0"):
                    continue

                action = row.get("Action", "").upper().strip()
                symbol = row.get("Symbol", "").strip()
                desc = row.get("Description", "").strip()
                description = f"{action} {symbol} {desc}".strip() if symbol else f"{action} {desc}".strip()

                # Determine type by action
                if action in _TRANSFER_ACTIONS:
                    tx_type = "transfer"
                elif action in _INCOME_ACTIONS or amount > 0:
                    tx_type = "income"
                else:
                    tx_type = "expense"

                transactions.append(RawTransaction(
                    date=tx_date,
                    description=description.upper(),
                    raw_description=description,
                    amount=amount,
                    currency="USD",
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"Schwab row error: {row} -> {e}")

        return transactions
