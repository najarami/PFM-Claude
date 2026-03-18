"""Parser for Tenpo CSV export format.

Expected headers (utf-8):
Fecha,Comercio,Categoria,Monto,Estado
"""
import csv
import io

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction

_HEADER_KEYS = {"Fecha", "Comercio", "Monto"}


class TenpoCSVParser(BaseParser):
    bank = BankName.TENPO

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        try:
            text = file_content.decode("utf-8")
            first_line = text.splitlines()[0]
            cols = {c.strip() for c in first_line.split(",")}
            return _HEADER_KEYS.issubset(cols) and "TENPO" in text[:300].upper()
        except Exception:
            return False

    def parse(self, file: io.IOBase, filename: str) -> list[RawTransaction]:
        content = file.read()
        text = content.decode("utf-8") if isinstance(content, bytes) else content

        reader = csv.DictReader(io.StringIO(text), delimiter=",")
        transactions = []
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items() if k}
            try:
                raw_date = row.get("Fecha", "")
                if not raw_date:
                    continue

                tx_date = None
                for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                    try:
                        tx_date = self._normalize_date(raw_date, fmt)
                        break
                    except ValueError:
                        continue
                if tx_date is None:
                    continue

                raw_desc = row.get("Comercio", "")
                raw_amount = row.get("Monto", "0")
                amount = self._normalize_amount(raw_amount)

                estado = row.get("Estado", "").upper()
                if estado in ("CANCELADO", "RECHAZADO"):
                    continue

                if amount < 0:
                    tx_type = "expense"
                    amount_signed = amount
                else:
                    tx_type = "income"
                    amount_signed = amount

                transactions.append(RawTransaction(
                    date=tx_date,
                    description=raw_desc.strip().upper(),
                    raw_description=raw_desc,
                    amount=amount_signed,
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"Tenpo row error: {row} -> {e}")

        return transactions
