"""Assembly of a single quote document.

Every quote is generated from its own RNG, seeded from (seed, id). Quote N is therefore
identical no matter how many quotes are generated or in which order.

Money is computed with Decimal and rounded half-up to cents:
  line total  = round(quantity * unit_price / price_unit * (1 - discount%))
  per tax rate: discount = round(sum(lines at rate) * header_discount%)
                base     = sum(lines at rate) - discount (+ shipping for 19 %)
                tax      = round(base * rate)
  Optional positions are priced but excluded from all totals.

NOTE: the order of RNG calls defines the output (see parties.py).
"""

import random
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from typing import Final

from . import GENERATOR_VERSION, SCHEMA_VERSION
from . import reference_data as ref
from .catalog import CATALOGS, SERVICE_UNITS, SITE_INDUSTRIES, SUBJECTS, UNITS, Item
from .parties import Customer, Person, PositionStyle, PriceStyle, Vendor, World, make_address
from .schema import (DeliveryAddress, DeliveryLabel, PaymentTerms, Position, Quote, TaxLine,
                     Totals, UnitKey)

CENT: Final[Decimal] = Decimal("0.01")
BASE_DATE: Final[date] = date(2024, 1, 2)
DATE_SPAN_DAYS: Final[int] = 1035  # quote dates between 2024-01-02 and ~2026-11
MAX_POSITIONS: Final[int] = 30
VAT_STANDARD: Final[Decimal] = Decimal(19)  # rate applied to shipping

HEADER_DISCOUNTS: Final[tuple[str, ...]] = ("2", "3", "5", "7.5", "10")
LINE_DISCOUNTS: Final[tuple[str, ...]] = ("5", "10", "12.5", "15", "20", "25", "30")
SHIPPING_FEES: Final[tuple[str, ...]] = ("4.90", "6.90", "9.90", "14.90", "19.90", "29.00", "49.00", "89.00")
SITE_LABELS: Final[tuple[DeliveryLabel, ...]] = ("Bauvorhaben", "Leistungsort")
REFERENCE_PREFIX_LETTERS: Final[str] = "ABCDEFGHKLMP"
DELIVERY_WORKDAYS: Final[tuple[int, ...]] = (2, 3, 5, 7, 10)

# (net_days, discount_days, discount_percent)
PAYMENT_TERMS: Final[tuple[tuple[int, int | None, str | None], ...]] = (
    (30, None, None),
    (30, 14, "2"),
    (30, 10, "3"),
    (30, 8, "2"),
    (14, None, None),
    (0, None, None),
    (45, 14, "3"),
)


# ---------------------------------------------------------------- formatting

def money(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def s_money(x: Decimal) -> str:
    return str(money(x))


def s_dec(x: Decimal) -> str:
    """Decimal without trailing zeros / exponent: 100 -> '100', 2.50 -> '2.5'."""
    return format(x.normalize(), "f")


def s_pct(x: Decimal) -> str:
    return str(x.quantize(CENT))


def de_date(d: date) -> str:
    return d.strftime("%d.%m.%Y")


def de_money(x: Decimal) -> str:
    s = f"{money(x):,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- helpers

def quote_number(vendor: Vendor, quote_id: int, d: date) -> str:
    seq = vendor.style.seq_base + quote_id
    y, yy, m = d.year, d.year % 100, d.month
    formats = (
        f"AN-{y}-{seq:05d}",
        f"ANG{yy:02d}{seq:06d}",
        f"{seq:07d}",
        f"Q-{y}{m:02d}-{seq:05d}",
        f"A{y}/{seq:05d}",
        f"{yy:02d}-{seq:05d}",
    )
    return formats[vendor.style.quote_number_format]


def customer_number(world: World, vendor: Vendor, customer: Customer) -> str | None:
    rng = random.Random(f"custno:{world.seed}:{vendor.index}:{customer.index}")
    if rng.random() < 0.15:  # prospect without customer number yet
        return None
    st = vendor.style
    n = st.customer_number_base + customer.index * st.customer_number_mult
    formats = (f"KD-{n:05d}", f"{n:06d}", f"K{n:07d}", f"D{n:05d}", str(n))
    return formats[st.customer_number_format]


def article_number(world: World, vendor: Vendor, desc: str, unit: UnitKey) -> str | None:
    st = vendor.style
    if not st.show_article_numbers:
        return None
    if unit in SERVICE_UNITS and not st.service_article_numbers:
        return None
    rng = random.Random(f"sku:{world.seed}:{vendor.index}:{desc}")
    p = st.article_prefix
    formats = (
        f"{rng.randint(100000, 999999)}",
        f"{p}-{rng.randint(10000, 99999)}",
        f"{rng.randint(100, 999)}.{rng.randint(0, 999):03d}.{rng.randint(0, 99):02d}",
        f"{p}{rng.randint(1000000, 9999999)}",
    )
    return formats[st.article_format]


def position_label(style: PositionStyle, i: int) -> str:
    if style == "step10":
        return str(i * 10)
    if style == "pad3":
        return f"{i:03d}"
    if style == "oz":
        return f"01.{i * 10:04d}"
    return str(i)


def draw_quantity(rng: random.Random, item: Item) -> Decimal:
    if item.qty_choices:
        return Decimal(rng.choice(item.qty_choices))
    step = Decimal(item.step)
    lo_d = (Decimal(str(item.qty[0])) / step).to_integral_value(ROUND_CEILING)
    hi_d = (Decimal(str(item.qty[1])) / step).to_integral_value(ROUND_FLOOR)
    lo, hi = max(int(lo_d), 1), max(int(hi_d), 1)
    u = rng.random()
    n = min(hi, lo + int((hi - lo + 1) * u * u))  # skewed towards small quantities
    return Decimal(n) * step


def draw_unit_price(rng: random.Random, item: Item, price_style: PriceStyle) -> Decimal:
    lo, hi = int(round(item.price[0] * 100)), int(round(item.price[1] * 100))
    cents = rng.randint(lo, hi)
    if cents >= 500:
        if price_style == "x90":
            cents = cents // 100 * 100 + 90
        elif price_style == "x95":
            cents = cents // 100 * 100 + 95
        elif price_style == "whole":
            cents = cents // 100 * 100
    return Decimal(cents) / 100


def skip_weekend(d: date) -> date:
    return d + timedelta(days=(7 - d.weekday()) % 7) if d.weekday() >= 5 else d


def greeting(person: Person | None) -> str:
    if person is None:
        return "Sehr geehrte Damen und Herren,"
    title = f"{person.title} " if person.title in ("Dr.", "Prof. Dr.") else ""
    if person.salutation == "Herr":
        return f"Sehr geehrter Herr {title}{person.last_name},"
    return f"Sehr geehrte Frau {title}{person.last_name},"


# ---------------------------------------------------------------- building blocks

def build_positions(rng: random.Random, world: World, vendor: Vendor) -> list[Position]:
    st = vendor.style
    catalog = CATALOGS[vendor.industry]

    # Skewed towards short quotes; only IEEE basic arithmetic (no log/pow) for portability.
    u = rng.random()
    n = 1 + int(MAX_POSITIONS * u * u * u)
    positions: list[Position] = []
    seen: set[str] = set()
    for _ in range(n):
        for _attempt in range(6):
            item = rng.choice(catalog)
            chosen: dict[str, str | int] = {k: rng.choice(v) for k, v in item.vars.items()}
            desc = item.desc.format(**chosen)
            if desc not in seen:
                break
        else:
            continue
        seen.add(desc)

        long_desc: str | None = None
        if item.long and rng.random() < st.long_text_prob:
            long_desc = rng.choice(item.long).format(**chosen)

        qty = draw_quantity(rng, item)
        unit_price = draw_unit_price(rng, item, st.price_style)
        discount: Decimal | None = None
        if item.unit != "lump" and rng.random() < st.line_discount_prob:
            discount = Decimal(rng.choice(LINE_DISCOUNTS))
        factor = (100 - discount) / 100 if discount is not None else Decimal(1)
        total = money(qty * unit_price / item.price_unit * factor)

        unit_def = UNITS[item.unit]
        positions.append({
            "position": "",  # numbered below, after optional positions are known
            "type": "standard",
            "article_number": article_number(world, vendor, desc, item.unit),
            "description": desc,
            "long_description": long_desc,
            "quantity": s_dec(qty),
            "unit": {"code": unit_def.code, "label": unit_def.labels[st.unit_label_variant]},
            "unit_price": s_money(unit_price),
            "price_unit": item.price_unit,
            "discount_percent": s_pct(discount) if discount is not None else None,
            "tax_rate": s_pct(Decimal(item.tax)),
            "total_price": s_money(total),
        })

    if len(positions) >= 3 and rng.random() < st.optional_position_prob:
        k = rng.randint(1, min(2, len(positions) - 2))
        for idx in sorted(rng.sample(range(len(positions)), k)):
            positions[idx]["type"] = "optional"

    for i, p in enumerate(positions, start=1):
        p["position"] = position_label(st.position_style, i)
    return positions


def compute_totals(positions: Sequence[Position], header_discount: Decimal | None,
                   shipping: Decimal | None) -> Totals:
    by_rate: dict[Decimal, Decimal] = {}
    for p in positions:
        if p["type"] != "standard":
            continue
        rate = Decimal(p["tax_rate"])
        by_rate[rate] = by_rate.get(rate, Decimal(0)) + Decimal(p["total_price"])
    positions_net = sum(by_rate.values(), Decimal(0))

    discount_amount = Decimal(0)
    bases: dict[Decimal, Decimal] = {}
    for rate in sorted(by_rate, reverse=True):
        d = money(by_rate[rate] * header_discount / 100) if header_discount else Decimal(0)
        discount_amount += d
        bases[rate] = by_rate[rate] - d
    if shipping:
        bases[VAT_STANDARD] = bases.get(VAT_STANDARD, Decimal(0)) + shipping

    tax_lines: list[TaxLine] = []
    for rate in sorted(bases, reverse=True):
        tax_lines.append({
            "rate": s_pct(rate),
            "base": s_money(bases[rate]),
            "amount": s_money(money(bases[rate] * rate / 100)),
        })
    net_total = positions_net - discount_amount + (shipping or Decimal(0))
    tax_total = sum((Decimal(t["amount"]) for t in tax_lines), Decimal(0))

    return {
        "positions_net": s_money(positions_net),
        "discount": ({"percent": s_pct(header_discount), "amount": s_money(discount_amount)}
                     if header_discount else None),
        "shipping": s_money(shipping) if shipping else None,
        "net_total": s_money(net_total),
        "tax": tax_lines,
        "tax_total": s_money(tax_total),
        "gross_total": s_money(net_total + tax_total),
    }


def payment_terms(vendor: Vendor, construction: bool) -> PaymentTerms:
    net_days, disc_days, disc_pct = PAYMENT_TERMS[vendor.style.payment_terms]
    if net_days == 0:
        text = "Zahlbar sofort nach Rechnungserhalt ohne Abzug."
    elif disc_days:
        text = (f"Zahlbar innerhalb von {disc_days} Tagen mit {disc_pct} % Skonto "
                f"oder innerhalb von {net_days} Tagen netto.")
    else:
        text = f"Zahlbar innerhalb von {net_days} Tagen nach Rechnungsdatum ohne Abzug."
    if construction:
        text = "Abschlagszahlungen nach Baufortschritt. " + text
    return {
        "net_days": net_days,
        "discount_days": disc_days,
        "discount_percent": s_pct(Decimal(disc_pct)) if disc_pct else None,
        "text": text,
    }


def delivery_terms_and_shipping(rng: random.Random, vendor: Vendor, customer: Customer,
                                positions_net: Decimal) -> tuple[str | None, Decimal | None]:
    kind = vendor.style.delivery_terms
    fee = Decimal(rng.choice(SHIPPING_FEES))
    if kind == "Leistungsort":
        return None, None
    if kind == "frei Haus":
        return "Lieferung frei Haus", None
    if kind == "ab Werk":
        return "ab Werk (EXW Incoterms® 2020), zzgl. Fracht und Verpackung", None
    if kind == "DAP":
        return f"DAP {customer.data['address']['city']} (Incoterms® 2020)", None
    if kind == "zzgl. Versand":
        return "zzgl. Versandkosten", fee
    threshold = vendor.style.free_shipping_threshold
    text = (f"Lieferung frei Haus ab {de_money(Decimal(threshold))} EUR Nettowarenwert, "
            f"darunter berechnen wir eine Versandkostenpauschale")
    return text, (fee if positions_net < threshold else None)


def delivery_time(rng: random.Random, vendor: Vendor, quote_date: date) -> str:
    # All tuple elements are evaluated (consuming RNG draws) before the choice is made.
    if vendor.industry in SITE_INDUSTRIES:
        start = quote_date + timedelta(weeks=rng.randint(2, 10))
        y, kw, _ = start.isocalendar()
        return rng.choice((
            "Ausführung nach Absprache",
            f"Beginn ca. {rng.randint(2, 8)} Wochen nach Auftragserteilung",
            f"Ausführung voraussichtlich ab KW {kw}/{y}",
            f"Leistungsbeginn {de_date(date(start.year, start.month, 1))}",
        ))
    target = quote_date + timedelta(weeks=rng.randint(1, 8))
    y, kw, _ = target.isocalendar()
    a = rng.randint(1, 4)
    return rng.choice((
        "sofort ab Lager, Zwischenverkauf vorbehalten",
        f"ca. {rng.choice(DELIVERY_WORKDAYS)} Werktage nach Auftragseingang",
        f"{a}–{a + rng.randint(1, 3)} Wochen nach Auftragseingang",
        f"KW {kw}/{y}",
        "nach Vereinbarung",
    ))


def customer_reference(rng: random.Random, quote_date: date) -> tuple[str | None, date | None]:
    if rng.random() >= 0.6:
        return None, None
    inquiry = quote_date - timedelta(days=rng.randint(1, 21))
    if rng.random() < 0.5:
        return None, inquiry
    ref_no = rng.choice((
        f"ANF-{inquiry.year}-{rng.randint(1, 9999):04d}",
        f"BANF {rng.randint(10000000, 10999999):010d}",
        f"{inquiry.year % 100:02d}/{rng.randint(100, 9999)}",
        f"Projekt {rng.choice(REFERENCE_PREFIX_LETTERS)}{rng.randint(100, 999)}",
    ))
    return ref_no, inquiry


# ---------------------------------------------------------------- main entry

def build_quote(world: World, quote_id: int) -> Quote:
    rng = random.Random(f"quote:{world.seed}:{quote_id}")

    vendor = rng.choices(world.vendors, weights=world.vendor_weights, k=1)[0]
    customer = rng.choice(world.customers)
    st = vendor.style
    is_site = vendor.industry in SITE_INDUSTRIES

    quote_date = skip_weekend(BASE_DATE + timedelta(days=rng.randint(0, DATE_SPAN_DAYS)))
    valid_until = quote_date + timedelta(days=st.validity_days)
    vendor_contact = rng.choice(vendor.contacts)

    customer_contact: Person | None
    addressee: Person | None
    if customer.person is not None:
        customer_contact, addressee = None, customer.person
    elif customer.contacts and rng.random() < 0.75:
        customer_contact = rng.choice(customer.contacts)
        addressee = customer_contact
    else:
        customer_contact, addressee = None, None

    # Delivery address / site address
    delivery_address: DeliveryAddress | None = None
    if is_site and rng.random() < 0.7:
        city = customer.city if rng.random() < 0.7 else rng.choice(ref.CITIES)
        label: DeliveryLabel = "Objekt" if vendor.industry == "facility" else rng.choice(SITE_LABELS)
        delivery_address = {"label": label, "name": None, "address": make_address(rng, city)}
    elif not is_site and customer.data["type"] == "company" and rng.random() < 0.12:
        city = customer.city if rng.random() < 0.6 else rng.choice(ref.CITIES)
        line2 = rng.choice(ref.DELIVERY_ADDRESS_LINES).format(n=rng.randint(1, 6))
        delivery_address = {"label": "Lieferanschrift", "name": customer.data["name"],
                            "address": make_address(rng, city, line2)}

    site_addr = delivery_address["address"] if delivery_address else customer.data["address"]
    site = f"{site_addr['street']} {site_addr['house_number']}, {site_addr['city']}"
    subject_tpl = rng.choice(SUBJECTS[vendor.industry])
    subject = subject_tpl.format(year=quote_date.year, site=site) if subject_tpl else None

    ref_no, inquiry_date = customer_reference(rng, quote_date)

    positions = build_positions(rng, world, vendor)
    std_net = sum((Decimal(p["total_price"]) for p in positions if p["type"] == "standard"), Decimal(0))
    header_discount = Decimal(rng.choice(HEADER_DISCOUNTS)) if rng.random() < st.header_discount_prob else None
    delivery_terms, shipping = delivery_terms_and_shipping(rng, vendor, customer, std_net)
    totals = compute_totals(positions, header_discount, shipping)

    inquiry_part = f" vom {de_date(inquiry_date)}" if inquiry_date else ""
    intro_bodies = (
        f"vielen Dank für Ihre Anfrage{inquiry_part}. Gerne unterbreiten wir Ihnen folgendes Angebot:",
        "wir bedanken uns für Ihr Interesse und bieten Ihnen freibleibend wie folgt an:",
        f"bezugnehmend auf Ihre Anfrage{inquiry_part} erhalten Sie nachstehend unser Angebot.",
        "gerne bieten wir Ihnen die nachfolgend aufgeführten Leistungen an:",
    )
    closing_bodies = (
        "Wir hoffen, Ihnen ein interessantes Angebot unterbreitet zu haben, und freuen uns auf Ihren Auftrag.",
        "Für Rückfragen stehen wir Ihnen jederzeit gerne zur Verfügung.",
        f"An dieses Angebot halten wir uns bis zum {de_date(valid_until)} gebunden. "
        "Es gelten unsere Allgemeinen Geschäftsbedingungen.",
        "Wir würden uns freuen, den Auftrag für Sie ausführen zu dürfen.",
    )

    return {
        "id": quote_id,
        "schema_version": SCHEMA_VERSION,
        "generator": {"version": GENERATOR_VERSION, "seed": world.seed},
        "document_type": "quote",
        "language": "de",
        "currency": "EUR",
        "quote_number": quote_number(vendor, quote_id, quote_date),
        "quote_date": quote_date.isoformat(),
        "valid_until": valid_until.isoformat(),
        "subject": subject,
        "customer_number": customer_number(world, vendor, customer),
        "customer_reference": ref_no,
        "inquiry_date": inquiry_date.isoformat() if inquiry_date else None,
        "vendor": vendor.data,
        "vendor_contact": vendor_contact.to_dict(),
        "customer": customer.data,
        "customer_contact": customer_contact.to_dict() if customer_contact else None,
        "delivery_address": delivery_address,
        "intro_text": f"{greeting(addressee)}\n\n{intro_bodies[st.intro_variant]}",
        "positions": positions,
        "totals": totals,
        "payment_terms": payment_terms(vendor, vendor.industry == "construction"),
        "delivery_terms": delivery_terms,
        "delivery_time": delivery_time(rng, vendor, quote_date),
        "closing_text": f"{closing_bodies[st.closing_variant]}\n\nMit freundlichen Grüßen",
    }
