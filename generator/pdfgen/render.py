"""Quote JSON -> HTML (Jinja2) -> PDF (WeasyPrint).

Every vendor gets a fixed "corporate identity" derived from a SHA-256 hash of its VAT ID: one of the
templates, an accent colour, a logo style and a few formatting habits. A vendor therefore looks the
same on every quote, the way real documents from the same ERP system do.

Ground-truth rule for all templates: every value from the JSON that a reader of the quote would care
about is printed somewhere on the PDF (optional positions also show their total price), so the
JSON file stays a complete answer key for extraction tests.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Final

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup, escape

from . import RENDERER_VERSION

TEMPLATE_DIR: Final[Path] = Path(__file__).resolve().parent / "templates"

# name -> description (shown by --list-templates)
TEMPLATES: Final[dict[str, str]] = {
    "din5008": "Classic German business letter (DIN 5008 form B): address window, info block, fold marks",
    "modern": "Modern SaaS invoicing tool look: big title, accent colour, zebra table, totals box",
    "erp": "Dense ERP printout: boxed header grid, tax codes, price unit column, running page header",
    "lv": "Tradesman / construction quote: serif, Leistungsverzeichnis blocks, EP/GP, acceptance slip",
}

ACCENTS: Final[tuple[str, ...]] = (
    "#1f4e79", "#7a1f2b", "#2e6b30", "#b35c00", "#4b2e83", "#00707a", "#3c3c3c", "#a01f62",
)
LOGO_STYLES: Final[tuple[str, ...]] = ("circle", "square", "bar", "text")
MONTHS_DE: Final[tuple[str, ...]] = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)
LEGAL_FORM_WORDS: Final[frozenset[str]] = frozenset(
    {"GmbH", "AG", "KG", "OHG", "UG", "e.K.", "e.K", "mbH", "Co.", "&", "(haftungsbeschränkt)", "GbR", "Inh."})


# ---------------------------------------------------------------- vendor identity

@dataclass(frozen=True)
class Identity:
    template: str
    accent: str
    logo: str            # circle | square | bar | text
    monogram: str
    long_date: bool      # "12. Mai 2025" instead of "12.05.2025" for the letter date
    currency_sign: str   # "€" or "EUR"


def _hash_ints(key: str) -> list[int]:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return list(digest)


def monogram(name: str) -> str:
    words = [w for w in name.replace("-", " ").split() if w not in LEGAL_FORM_WORDS and w[:1].isalpha()]
    letters = "".join(w[0] for w in words[:2]).upper()
    return letters or name[:2].upper()


def vendor_identity(vendor: dict[str, Any], template: str | None = None) -> Identity:
    h = _hash_ints(f"pdfgen/{vendor['vat_id']}/{vendor['name']}")
    names = list(TEMPLATES)
    return Identity(
        template=template or names[h[0] % len(names)],
        accent=ACCENTS[h[1] % len(ACCENTS)],
        logo=LOGO_STYLES[h[2] % len(LOGO_STYLES)],
        monogram=monogram(vendor["name"]),
        long_date=h[3] % 3 == 0,
        currency_sign="EUR" if h[4] % 3 == 0 else "€",
    )


# ---------------------------------------------------------------- formatting filters

def de_number(value: Any, decimals: int = 2) -> str:
    """'1234.5' -> '1.234,50' (German grouping and decimal comma, rounded half-up)."""
    d = Decimal(str(value)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    return f"{d:,.{decimals}f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def money(value: Any) -> str:
    return de_number(value, 2)


def qty(value: Any, min_decimals: int = 0) -> str:
    """Quantity with as many decimals as needed (at least ``min_decimals``): '2.5' -> '2,5'."""
    d = Decimal(str(value)).normalize()
    places = max(min_decimals, -d.as_tuple().exponent if d.as_tuple().exponent < 0 else 0)
    return de_number(d, places)


def pct(value: Any, fixed: bool = False) -> str:
    """'19.00' -> '19' (or '19,00' with fixed=True); '12.50' -> '12,5'."""
    return de_number(value, 2) if fixed else qty(value)


def de_date(value: str | None, long: bool = False) -> str:
    if not value:
        return ""
    d = date.fromisoformat(value)
    return f"{d.day}. {MONTHS_DE[d.month - 1]} {d.year}" if long else d.strftime("%d.%m.%Y")


def paragraphs(text: str | None) -> Markup:
    """Blank line -> new paragraph, single newline -> <br>."""
    if not text:
        return Markup("")
    paras = [p for p in text.split("\n\n") if p.strip()]
    return Markup("".join(f"<p>{Markup('<br>').join(escape(line) for line in p.splitlines())}</p>"
                          for p in paras))


def css_string(text: Any) -> Markup:
    """Quoted CSS string literal for ``content:`` (HTML escaping does not apply inside <style>)."""
    s = str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\a ").replace("<", "\\3c ")
    return Markup(f'"{s}"')


def person_name(p: dict[str, Any] | None, with_salutation: bool = False) -> str:
    if not p:
        return ""
    parts = [p["salutation"] if with_salutation else None, p.get("title"), p["first_name"], p["last_name"]]
    return " ".join(x for x in parts if x)


def street_line(a: dict[str, Any]) -> str:
    return f"{a['street']} {a['house_number']}"


def city_line(a: dict[str, Any]) -> str:
    return f"{a['postal_code']} {a['city']}"


def address_lines(a: dict[str, Any]) -> list[str]:
    lines = [street_line(a)]
    if a.get("address_line2"):
        lines.append(a["address_line2"])
    lines.append(city_line(a))
    if a.get("country_code", "DE") != "DE":
        lines.append(a["country"].upper())
    return lines


def recipient_lines(q: dict[str, Any], classic: bool) -> list[str]:
    """Postal address block. ``classic`` = old-school "Herrn" on its own line."""
    c = q["customer"]
    contact = q.get("customer_contact")
    lines: list[str] = []
    if c["type"] == "private" and c.get("person"):
        p = c["person"]
        if classic:
            lines += ["Herrn" if p["salutation"] == "Herr" else "Frau", person_name(p)]
        else:
            lines.append(person_name(p, with_salutation=True))
    else:
        lines.append(c["name"])
        if c.get("department"):
            lines.append(c["department"])
        if contact:
            sal = "Herrn" if contact["salutation"] == "Herr" else "Frau"
            lines.append(f"z. Hd. {sal} {person_name(contact)}" if classic
                         else person_name(contact, with_salutation=True))
    return lines + address_lines(c["address"])


# ---------------------------------------------------------------- context

def build_context(q: dict[str, Any], ident: Identity) -> dict[str, Any]:
    positions = q["positions"]
    position_rates = {p["tax_rate"] for p in positions}
    # Shipping can add a 19 % line even if no position is at 19 %, so codes cover both.
    rates = sorted(position_rates | {t["rate"] for t in q["totals"]["tax"]}, key=Decimal, reverse=True)
    v = q["vendor"]
    return {
        "q": q,
        "v": v,
        "t": q["totals"],
        "ident": ident,
        "cur": ident.currency_sign,
        "renderer_version": RENDERER_VERSION,
        "has_article": any(p["article_number"] for p in positions),
        "has_discount": any(p["discount_percent"] for p in positions),
        "has_price_unit": any(p["price_unit"] != 1 for p in positions),
        "has_optional": any(p["type"] == "optional" for p in positions),
        "mixed_tax": len(position_rates) > 1,
        "tax_codes": {r: str(i + 1) for i, r in enumerate(rates)},
        "sender_line": " · ".join([v["name"], street_line(v["address"]), city_line(v["address"])]),
        "recipient_classic": recipient_lines(q, classic=True),
        "recipient_modern": recipient_lines(q, classic=False),
        "vendor_address": address_lines(v["address"]),
        "contact": q["vendor_contact"],
        "contact_name": person_name(q["vendor_contact"]),
        "letter_date": de_date(q["quote_date"], long=ident.long_date),
    }


def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=True,          # also applies to the included *.css.j2 (harmless: no & < > in CSS)
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(css=css_string, money=money, qty=qty, pct=pct, de_date=de_date, paragraphs=paragraphs,
                       person_name=person_name, address_lines=address_lines)
    return env


_ENV: Environment | None = None


def render_html(q: dict[str, Any], template: str | None = None) -> tuple[str, Identity]:
    global _ENV
    if _ENV is None:
        _ENV = make_env()
    ident = vendor_identity(q["vendor"], template)
    if ident.template not in TEMPLATES:
        raise ValueError(f"unknown template {ident.template!r}, choose from {', '.join(TEMPLATES)}")
    html = _ENV.get_template(f"{ident.template}.html.j2").render(**build_context(q, ident))
    return html, ident


@dataclass(frozen=True)
class Rendered:
    pdf: bytes
    identity: Identity
    pages: int


def render_pdf(q: dict[str, Any], template: str | None = None) -> Rendered:
    from weasyprint import HTML  # imported lazily: slow import, and --html mode doesn't need it

    html, ident = render_html(q, template)
    doc = HTML(string=html, base_url=str(TEMPLATE_DIR)).render()
    # A fixed identifier (instead of a random one) keeps the output byte-identical between runs.
    pdf_id = hashlib.md5(f"{q['quote_number']}/{q['id']}".encode()).hexdigest().encode()
    return Rendered(pdf=doc.write_pdf(pdf_identifier=pdf_id), identity=ident, pages=len(doc.pages))
