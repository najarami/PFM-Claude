"""Parser for BCI CSV export format.

Expected headers (latin-1 or utf-8):
Fecha;Descripcion;Cargo;Abono;Saldo
"""
import csv
import io

from app.parsers.base import BankName, BaseParser, ParseError, RawTransaction

_HEADER_KEYS = {"Fecha", "Descripcion", "Cargo", "Abono"}


class BciCSVParser(BaseParser):
    bank = BankName.BCI

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".csv"):
            return False
        try:
            for encoding in ("latin-1", "utf-8"):
                try:
                    text = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            first_line = text.splitlines()[0]
            cols = {c.strip() for c in first_line.split(";")}
            return _HEADER_KEYS.issubset(cols) and "BCI" in text[:200].upper()
        except Exception:
            return False

    def parse(self, file: io.IOBase, filename: str) -> list[RawTransaction]:
        content = file.read()
        for encoding in ("latin-1", "utf-8"):
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        transactions = []
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items() if k}
            try:
                raw_date = row.get("Fecha", "")
                if not raw_date:
                    continue

                tx_date = None
                for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
                    try:
                        tx_date = self._normalize_date(raw_date, fmt)
                        break
                    except ValueError:
                        continue
                if tx_date is None:
                    continue

                raw_desc = row.get("Descripcion", "")
                cargo = row.get("Cargo", "").strip()
                abono = row.get("Abono", "").strip()

                if cargo and cargo not in ("", "0", "-"):
                    amount = -self._normalize_amount(cargo)
                    tx_type = "expense"
                elif abono and abono not in ("", "0", "-"):
                    amount = self._normalize_amount(abono)
                    tx_type = "income"
                else:
                    continue

                transactions.append(RawTransaction(
                    date=tx_date,
                    description=raw_desc.strip().upper(),
                    raw_description=raw_desc,
                    amount=amount,
                    transaction_type=tx_type,
                    source_file=filename,
                ))
            except Exception as e:
                raise ParseError(f"BCI row error: {row} -> {e}")

        return transactions
