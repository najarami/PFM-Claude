"""Parser for Banco de Chile CSV export format.

Expected headers (latin-1 encoded):
Fecha;Descripción;Número de documento;Monto;Saldo
or with "Cargo" / "Abono" split columns.
"""
import csv
import io
from decimal import Decimal

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction

# Banco de Chile may export with semicolon or comma delimiters
_HEADER_KEYS = {"Fecha", "Descripción", "Monto"}
_HEADER_KEYS_SPLIT = {"Fecha", "Descripción", "Cargo", "Abono"}


class BancoChileCSVParser(BaseParser):
    bank = BankName.BANCO_CHILE

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        try:
            text = file_content.decode("latin-1")
            first_line = text.splitlines()[0]
            return ("Banco de Chile" in text[:500] or
                    _HEADER_KEYS.issubset(set(c.strip() for c in first_line.split(";"))) or
                    _HEADER_KEYS_SPLIT.issubset(set(c.strip() for c in first_line.split(";"))))
        except Exception:
            return False

    def parse(self, file: io.IOBase, filename: str) -> list[RawTransaction]:
        content = file.read()
        text = content.decode("latin-1") if isinstance(content, bytes) else content

        # Detect delimiter
        first_line = text.splitlines()[0]
        delimiter = ";" if ";" in first_line else ","

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            raise ParseError(f"No data rows found in {filename}")

        transactions = []
        for row in rows:
            row = {k.strip(): v.strip() for k, v in row.items() if k}
            try:
                raw_date = row.get("Fecha", "")
                if not raw_date:
                    continue

                # Try multiple date formats
                tx_date = None
                for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                    try:
                        tx_date = self._normalize_date(raw_date, fmt)
                        break
                    except ValueError:
                        continue
                if tx_date is None:
                    continue

                raw_desc = row.get("Descripción", row.get("Descripcion", ""))

                # Handle split Cargo/Abono columns
                if "Cargo" in row and "Abono" in row:
                    cargo = row.get("Cargo", "").strip()
                    abono = row.get("Abono", "").strip()
                    if cargo and cargo not in ("", "0", "-", "0,00"):
                        amount = -self._normalize_amount(cargo)
                        tx_type = "expense"
                    elif abono and abono not in ("", "0", "-", "0,00"):
                        amount = self._normalize_amount(abono)
                        tx_type = "income"
                    else:
                        continue
                else:
                    raw_amount = row.get("Monto", "0")
                    amount = self._normalize_amount(raw_amount)
                    tx_type = self._detect_type(raw_desc, amount)
                    if amount > 0 and tx_type == "expense":
                        tx_type = "income"
                    elif amount < 0:
                        amount = abs(amount)
                        tx_type = "expense"
                    elif amount == 0:
                        continue

                transactions.append(RawTransaction(
                    date=tx_date,
                    description=raw_desc.strip().upper(),
                    raw_description=raw_desc,
                    amount=amount if tx_type == "income" else -amount,
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"Row parse error in {filename}: {row} -> {e}")

        return transactions
