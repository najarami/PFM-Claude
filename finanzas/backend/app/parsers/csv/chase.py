"""Parser for Chase Bank CSV export format.

Headers: Transaction Date,Post Date,Description,Category,Type,Amount,Memo

Amount: negative = expense (Sale/Fee), positive = income (Payment/Return).
Type field: "Sale", "Payment", "Return", "Fee", "Adjustment".
"""
import csv
import io

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction

_HEADER_SIGNATURE = "Transaction Date,Post Date,Description,Category,Type,Amount"


class ChaseCSVParser(BaseParser):
    bank = BankName.CHASE

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        try:
            text = file_content.decode("utf-8")
            first_line = text.splitlines()[0] if text.strip() else ""
            return _HEADER_SIGNATURE in first_line or "chase" in filename.lower()
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
                raw_date = row.get("Transaction Date", row.get("Date", ""))
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
                memo = row.get("Memo", "")
                description = raw_desc if not memo else f"{raw_desc} {memo}"

                raw_amount = row.get("Amount", "0")
                amount = self._normalize_amount_usd(raw_amount)

                if amount == 0:
                    continue

                tx_type_raw = row.get("Type", "").upper()
                if tx_type_raw in ("PAYMENT", "RETURN", "ADJUSTMENT"):
                    tx_type = "income"
                    if amount < 0:
                        amount = abs(amount)
                elif tx_type_raw in ("TRANSFER"):
                    tx_type = "transfer"
                else:
                    tx_type = "income" if amount > 0 else "expense"

                transactions.append(RawTransaction(
                    date=tx_date,
                    description=description.strip().upper(),
                    raw_description=description.strip(),
                    amount=amount,
                    currency="USD",
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"Chase row error: {row} -> {e}")

        return transactions
