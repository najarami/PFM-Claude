"""Parser registry with automatic bank detection."""
from app.parsers.base import BaseParser, ParseError
# Chilean banks — CSV
from app.parsers.csv.banco_chile import BancoChileCSVParser
from app.parsers.csv.bci import BciCSVParser
from app.parsers.csv.santander import SantanderCSVParser
from app.parsers.csv.mach import MachCSVParser
from app.parsers.csv.tenpo import TenpoCSVParser
from app.parsers.csv.mercado_pago import MercadoPagoCSVParser
# Chilean banks — PDF
from app.parsers.pdf.banco_chile import BancoChilePDFParser
from app.parsers.pdf.bci import BciPDFParser
from app.parsers.pdf.santander import SantanderPDFParser
# US banks — CSV
from app.parsers.csv.bank_of_america import BankOfAmericaCSVParser
from app.parsers.csv.chase import ChaseCSVParser
from app.parsers.csv.wells_fargo import WellsFargoCSVParser
from app.parsers.csv.schwab import SchwabCSVParser
from app.parsers.csv.amex import AmexCSVParser
from app.parsers.csv.citi import CitiCSVParser

# Order matters: more specific parsers first.
# US parsers use filename-based sniffing which is very specific → go early.
ALL_PARSERS: list[BaseParser] = [
    # PDF parsers (checked before CSV to avoid extension-only matching)
    BancoChilePDFParser(),
    BciPDFParser(),
    SantanderPDFParser(),
    # US banks (filename sniffing is very specific — check before generic Chilean parsers)
    ChaseCSVParser(),
    WellsFargoCSVParser(),
    SchwabCSVParser(),
    BankOfAmericaCSVParser(),
    AmexCSVParser(),
    CitiCSVParser(),
    # Chilean CSV parsers
    BancoChileCSVParser(),
    BciCSVParser(),
    SantanderCSVParser(),
    MachCSVParser(),
    TenpoCSVParser(),
    MercadoPagoCSVParser(),
]


def detect_parser(filename: str, content: bytes) -> BaseParser:
    """
    Try each parser's can_parse() and return the first match.
    Raises ParseError if no parser can handle the file.
    """
    for parser in ALL_PARSERS:
        if parser.can_parse(filename, content):
            return parser
    raise ParseError(
        f"No parser found for file '{filename}'. "
        "Supported banks (CL): Banco de Chile, BCI, Santander, MACH, Tenpo, Mercado Pago. "
        "Supported banks (US): Bank of America, Chase, Wells Fargo, Schwab, Amex, Citi. "
        "Supported formats: CSV, PDF."
    )
