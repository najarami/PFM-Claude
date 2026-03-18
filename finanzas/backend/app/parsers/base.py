from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import IO


class BankName(str, Enum):
    # Chilean banks
    BANCO_CHILE = "banco_chile"
    BCI = "bci"
    SANTANDER = "santander"
    MACH = "mach"
    TENPO = "tenpo"
    MERCADO_PAGO = "mercado_pago"
    # US banks & cards
    BANK_OF_AMERICA = "bank_of_america"
    CHASE = "chase"
    WELLS_FARGO = "wells_fargo"
    SCHWAB = "schwab"
    AMEX = "amex"
    CITI = "citi"
    UNKNOWN = "unknown"


@dataclass
class RawTransaction:
    date: date
    description: str
    raw_description: str
    amount: Decimal          # negative = expense, positive = income
    currency: str = "CLP"
    transaction_type: str = "expense"   # income | expense | transfer
    source_file: str = ""


class ParseError(Exception):
    pass


class BaseParser(ABC):
    bank: BankName

    @abstractmethod
    def can_parse(self, filename: str, file_content: bytes) -> bool:
        """Return True if this parser handles the given file."""

    @abstractmethod
    def parse(self, file: IO[bytes], filename: str) -> list[RawTransaction]:
        """Parse file and return normalized transactions."""

    def _normalize_amount(self, raw: str) -> Decimal:
        """Strip currency symbols, dots (thousands), convert comma to decimal point.
        Handles Chilean format: 1.234.567,89 → 1234567.89
        """
        cleaned = (
            raw.strip()
            .replace("$", "")
            .replace("\xa0", "")   # non-breaking space
            .replace(" ", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        if not cleaned or cleaned == "-":
            return Decimal("0")
        return Decimal(cleaned)

    def _normalize_amount_usd(self, raw: str) -> Decimal:
        """Normalize US-format amounts: $1,234.56 → 1234.56
        Commas are thousands separators, dot is decimal.
        """
        cleaned = (
            raw.strip()
            .replace("$", "")
            .replace("\xa0", "")
            .replace(" ", "")
            .replace(",", "")   # remove thousands separators
            .strip()
        )
        if not cleaned or cleaned in ("-", "--"):
            return Decimal("0")
        return Decimal(cleaned)

    def _normalize_date(self, raw: str, fmt: str) -> date:
        from datetime import datetime
        return datetime.strptime(raw.strip(), fmt).date()

    def _detect_type(self, description: str, amount: Decimal) -> str:
        upper = description.upper()
        transfer_keywords = ["TRANSFERENCIA", "PAGO TC", "PAG TC", "PAGO TARJETA"]
        income_keywords = ["REMUNERACION", "SUELDO", "DEPOSITO", "ABONO", "HONORARIO"]
        if any(kw in upper for kw in income_keywords) or amount > 0:
            return "income"
        if any(kw in upper for kw in transfer_keywords):
            return "transfer"
        return "expense"
