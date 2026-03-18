"""Keyword-based auto-categorization. Longer keyword wins on conflict."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.category import Category

# Built-in keyword rules: {slug: [keywords in uppercase]}
# Longer keywords are more specific and win over shorter ones.
KEYWORD_RULES: dict[str, list[str]] = {
    "salary": [
        "REMUNERACION", "SUELDO", "HONORARIO", "SALARIO", "REMUNERACIÓN",
        "PAGO SUELDO", "LIQ. SUELDO",
    ],
    "transfer_in": [
        "TRANSFERENCIA RECIBIDA", "DEPOSITO RECIBIDO", "ABONO TRANSFERENCIA",
        "TEF RECIBIDA", "DEPOSITO",
    ],
    "food_dining": [
        "SUPERMERCADO", "JUMBO", "LIDER", "UNIMARC", "SANTA ISABEL", "ACUENTA",
        "EASY", "RAPPI", "PEDIDOSYA", "UBER EATS", "IFOOD", "CORNERSHOP",
        "RESTAURANT", "RESTORAN", "SUSHI", "PIZZA", "CAFE", "PANADERIA",
        "ALMACEN", "MINIMARKET", "BOTILLERIA", "MCDONALDS", "BURGER KING",
        "SUBWAY", "STARBUCKS", "KFC",
    ],
    "transport": [
        "UBER", "CABIFY", "DIDI", "BEAT", "INDRIVER",
        "METRO DE SANTIAGO", "METRO", "BIP", "TRANSANTIAGO",
        "COPEC", "SHELL", "PETROBRAS", "ENEX", "TERPEL",
        "AUTOPISTA", "PEAJE", "BENCIN",
    ],
    "housing": [
        "ARRIENDO", "RENTA MENSUAL", "ADMINISTRACION",
        "AGUAS ANDINAS", "ESVAL", "ENEL", "CGE", "METROGAS",
        "ENTEL HOGAR", "MOVISTAR HOGAR", "VTR", "CLARO HOGAR",
        "GASTOS COMUNES",
    ],
    "utilities": [
        "ENTEL", "MOVISTAR", "CLARO", "WOM", "BITEL",
        "PLAN MOVIL", "INTERNET",
    ],
    "entertainment": [
        "NETFLIX", "SPOTIFY", "STEAM", "DISNEY PLUS", "DISNEY+",
        "HBO MAX", "AMAZON PRIME", "APPLE TV", "PARAMOUNT",
        "CINE", "TEATRO", "CONCIERTO", "PLAYSTATION", "XBOX",
        "EPIC GAMES", "NINTENDO",
    ],
    "health": [
        "FARMACIA AHUMADA", "SALCOBRAND", "CRUZ VERDE", "FARMACIAS",
        "FARMACIA", "CLINICA", "HOSPITAL", "DENTISTA", "OPTOMETRISTA",
        "ISAPRE", "FONASA", "MEDICO", "CONSULTA",
    ],
    "education": [
        "UNIVERSIDAD", "COLEGIO", "INSTITUTO", "ACADEMIA",
        "COURSERA", "UDEMY", "DUOLINGO", "MATRICULA", "ARANCEL",
    ],
    "clothing": [
        "FALABELLA", "RIPLEY", "PARIS", "H&M", "ZARA",
        "BERSHKA", "PULL AND BEAR", "ROPA", "CALZADO", "ZAPATOS",
    ],
    "finance": [
        "PAGO TARJETA", "PAG TC", "PAGO TC", "PAG. TARJETA",
        "SEGURO", "AFP", "COTIZACION", "CREDITO", "DIVIDENDO",
        "COMISION BANCARIA", "CARGO MENSUAL",
    ],
}


async def auto_categorize(description: str, session: AsyncSession) -> str | None:
    """
    Return category slug for best keyword match, or None.
    Priority: length of matched keyword (longer = more specific wins).
    """
    upper_desc = description.upper()
    best: tuple[int, str | None] = (0, None)  # (keyword_length, slug)

    for slug, keywords in KEYWORD_RULES.items():
        for kw in keywords:
            if kw in upper_desc and len(kw) > best[0]:
                best = (len(kw), slug)

    return best[1]


async def get_category_id_by_slug(slug: str, session: AsyncSession) -> str | None:
    """Resolve slug → UUID."""
    result = await session.execute(
        select(Category.id).where(Category.slug == slug)
    )
    row = result.scalar_one_or_none()
    return str(row) if row else None
