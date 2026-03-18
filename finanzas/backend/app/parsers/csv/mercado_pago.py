"""Parser for Mercado Pago CSV export format.

Expected headers (utf-8):
Fecha,Descripción,Detalle,Medio de pago,Total
"""
import csv
import io

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction

_HEADER_KEYS = {"Fecha", "Descripción", "Total"}


class MercadoPagoCSVParser(BaseParser):
    bank = BankName.MERCADO_PAGO

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        try:
            text = file_content.decode("utf-8")
            first_line = text.splitlines()[0]
            cols = {c.strip() for c in first_line.split(",")}
            return (_HEADER_KEYS.issubset(cols) and
                    ("MERCADO" in text[:300].upper() or "mercadopago" in filename.lower()))
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

                # Mercado Pago format: "2024-01-15 10:30:00" or "15/01/2024"
                raw_date_part = raw_date.split(" ")[0]
                tx_date = None
                for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                    try:
                        tx_date = self._normalize_date(raw_date_part, fmt)
                        break
                    except ValueError:
                        continue
                if tx_date is None:
                    continue

                raw_desc = row.get("Descripción", row.get("Descripcion", ""))
                detalle = row.get("Detalle", "")
                description = f"{raw_desc} {detalle}".strip()

                raw_amount = row.get("Total", "0")
                amount = self._normalize_amount(raw_amount)

                if amount < 0:
                    tx_type = "expense"
                else:
                    tx_type = "income"

                transactions.append(RawTransaction(
                    date=tx_date,
                    description=description.upper(),
                    raw_description=description,
                    amount=amount,
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"MercadoPago row error: {row} -> {e}")

        return transactions
