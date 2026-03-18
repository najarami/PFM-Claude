"""Base PDF parser using pdfplumber for table extraction."""
import io
from abc import abstractmethod

import pdfplumber

from app.parsers.base import BaseParser, RawTransaction


class BasePDFParser(BaseParser):
    """Extends BaseParser with PDF-specific utilities."""

    def can_parse(self, filename: str, file_content: bytes) -> bool:
        if not filename.lower().endswith(".pdf"):
            return False
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                first_page_text = pdf.pages[0].extract_text() or ""
                return self._matches_bank(first_page_text)
        except Exception:
            return False

    @abstractmethod
    def _matches_bank(self, first_page_text: str) -> bool:
        """Return True if the first page text identifies this bank's statement."""

    def _extract_tables(self, file: io.IOBase) -> list[list[list[str]]]:
        """Extract all tables from all pages as list of tables."""
        content = file.read()
        tables = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
        return tables

    def _extract_text_lines(self, file: io.IOBase) -> list[str]:
        """Extract all text lines from all pages."""
        content = file.read()
        lines = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines.extend(text.splitlines())
        return lines

    def parse(self, file: io.IOBase, filename: str) -> list[RawTransaction]:
        raise NotImplementedError("Each PDF parser must implement parse()")
