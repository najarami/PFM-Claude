"""PDF parser for BCI account/credit card statements."""
import io
import re
from decimal import Decimal

from app.parsers.base import BankName, ParseError, RawTransaction
from app.parsers.pdf.base_pdf import BasePDFParser

_TX_PATTERN = re.compile(
    r"(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d\.]+,\d{2})"
)


class BciPDFParser(BasePDFParser):
    bank = BankName.BCI

    def _matches_bank(self, first_page_text: str) -> bool:
        return "BCI" in first_page_text.upper() and "BANCO" in first_page_text.upper()

    def parse(self, file: io.IOBase, filename: str) -> list[RawTransaction]:
        lines = self._extract_text_lines(file)
        transactions = []

        for line in lines:
            match = _TX_PATTERN.search(line.strip())
            if not match:
                continue
            try:
                raw_date, raw_desc, raw_amount = match.groups()
                tx_date = self._normalize_date(raw_date, "%d/%m/%Y")
                amount = self._normalize_amount(raw_amount)

                if amount == Decimal("0"):
                    continue

                tx_type = self._detect_type(raw_desc, amount)
                transactions.append(RawTransaction(
                    date=tx_date,
                    description=raw_desc.strip().upper(),
                    raw_description=raw_desc.strip(),
                    amount=amount if tx_type == "income" else -abs(amount),
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"BCI PDF line error: '{line}' -> {e}")

        return transactions
