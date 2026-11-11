"""Vendors and customers. Built once per seed as a fixed "world" that quotes draw from,
so the same vendor appears consistently (same letterhead, staff, numbering style) across quotes.

NOTE: the order of RNG calls defines the output. Reordering draws (even inside a dict or
constructor call) changes every generated file and requires a GENERATOR_VERSION bump.
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, TypeVar

from . import reference_data as ref
from .catalog import CATALOGS, INDUSTRY_NAME_WORDS, SITE_INDUSTRIES
from .identifiers import (EMAIL_STYLES, PHONE_STYLES, ascii_slug, bic, email_local_part,
                          format_phone, iban_de, mobile_number, subscriber_number, tax_number,
                          vat_id_de)
from .reference_data import City
from .schema import (Address, CustomerData, Industry, PersonData, RegisterType, Salutation,
                     VendorData)

T = TypeVar("T")

PositionStyle: TypeAlias = Literal["seq", "step10", "pad3", "oz"]
PriceStyle: TypeAlias = Literal["exact", "x90", "x95", "whole"]
DeliveryTermsKind: TypeAlias = Literal["Leistungsort", "frei Haus", "ab Werk", "DAP", "zzgl. Versand", "frei Haus ab"]

NUM_VENDORS: Final[int] = 60
NUM_CUSTOMERS: Final[int] = 500
PRIVATE_CUSTOMER_SHARE: Final[float] = 0.12

# Choice tables for vendor habits (duplicates act as weights).
POSITION_STYLES_CONSTRUCTION: Final[tuple[PositionStyle, ...]] = ("oz", "seq", "step10")
POSITION_STYLES_DEFAULT: Final[tuple[PositionStyle, ...]] = ("seq", "seq", "step10", "pad3")
PRICE_STYLES: Final[tuple[PriceStyle, ...]] = ("exact", "exact", "x90", "x95", "whole")
DELIVERY_TERMS_SITE: Final[tuple[DeliveryTermsKind, ...]] = ("Leistungsort",)
DELIVERY_TERMS_GOODS: Final[tuple[DeliveryTermsKind, ...]] = (
    "frei Haus", "ab Werk", "DAP", "zzgl. Versand", "frei Haus ab")
VALIDITY_DAYS: Final[tuple[int, ...]] = (14, 21, 28, 30, 30, 60, 90)
FREE_SHIPPING_THRESHOLDS: Final[tuple[int, ...]] = (150, 250, 500)
LINE_DISCOUNT_PROBS: Final[tuple[float, ...]] = (0.0, 0.0, 0.1, 0.3)
HEADER_DISCOUNT_PROBS: Final[tuple[float, ...]] = (0.0, 0.1, 0.2)
OPTIONAL_POSITION_PROBS: Final[tuple[float, ...]] = (0.0, 0.1, 0.25)
LONG_TEXT_PROBS: Final[tuple[float, ...]] = (0.3, 0.6, 0.9)
ARTICLE_PREFIX_LETTERS: Final[str] = "ABCDEFGHKLMNPRSTVWZ"
CENTRAL_MAILBOXES: Final[tuple[str, ...]] = ("info", "vertrieb", "angebote", "kontakt", "office")
HOUSE_NUMBER_LETTERS: Final[str] = "abc"
HOUSE_NUMBER_RANGE_SPANS: Final[tuple[int, ...]] = (2, 4)
EK_NAME_PATTERNS: Final[tuple[int, ...]] = (0, 3)


def weighted(rng: random.Random, pairs: Sequence[tuple[T, int]]) -> T:
    values = [p[0] for p in pairs]
    weights = [p[1] for p in pairs]
    return rng.choices(values, weights=weights, k=1)[0]


@dataclass
class Person:
    salutation: Salutation
    title: str | None
    first_name: str
    last_name: str
    role: str | None = None
    phone: str | None = None
    mobile: str | None = None
    email: str | None = None

    @property
    def full_name(self) -> str:
        return " ".join(p for p in (self.title, self.first_name, self.last_name) if p)

    def to_dict(self) -> PersonData:
        return {
            "salutation": self.salutation,
            "title": self.title,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "phone": self.phone,
            "mobile": self.mobile,
            "email": self.email,
        }


@dataclass(frozen=True)
class VendorStyle:
    """A vendor's formatting and commercial habits. Internal only, never serialized."""
    quote_number_format: int        # index into quote.quote_number formats
    seq_base: int
    customer_number_format: int     # index into quote.customer_number formats
    customer_number_base: int
    customer_number_mult: int
    position_style: PositionStyle
    unit_label_variant: int         # 0..2, index into UnitDef.labels
    article_format: int             # index into quote.article_number formats
    article_prefix: str
    show_article_numbers: bool
    service_article_numbers: bool
    price_style: PriceStyle
    validity_days: int
    payment_terms: int              # index into quote.PAYMENT_TERMS
    delivery_terms: DeliveryTermsKind
    free_shipping_threshold: int
    line_discount_prob: float
    header_discount_prob: float
    optional_position_prob: float
    long_text_prob: float
    intro_variant: int
    closing_variant: int


@dataclass
class Vendor:
    index: int
    industry: Industry
    data: VendorData           # serialized as-is into the quote
    contacts: list[Person]
    style: VendorStyle
    area_code: str
    main_subscriber: str


@dataclass
class Customer:
    index: int
    data: CustomerData
    contacts: list[Person]
    person: Person | None      # set for private customers
    city: City


@dataclass
class World:
    seed: int
    vendors: list[Vendor]
    vendor_weights: list[int]
    customers: list[Customer]


def make_person(rng: random.Random, last_name: str | None = None) -> Person:
    salutation: Salutation
    if rng.random() < 0.5:
        salutation, first = "Herr", rng.choice(ref.FIRST_NAMES_MALE)
    else:
        salutation, first = "Frau", rng.choice(ref.FIRST_NAMES_FEMALE)
    return Person(
        salutation=salutation,
        title=weighted(rng, ref.PERSON_TITLES),
        first_name=first,
        last_name=last_name or rng.choice(ref.SURNAMES),
    )


def house_number(rng: random.Random) -> str:
    n = rng.randint(1, 180) if rng.random() < 0.85 else rng.randint(1, 15)
    r = rng.random()
    if r < 0.10:
        return f"{n}{rng.choice(HOUSE_NUMBER_LETTERS)}"
    if r < 0.15:
        return f"{n}-{n + rng.choice(HOUSE_NUMBER_RANGE_SPANS)}"
    return str(n)


def make_address(rng: random.Random, city: City, line2: str | None = None) -> Address:
    return {
        "street": rng.choice(ref.STREETS),
        "house_number": house_number(rng),
        "address_line2": line2,
        "postal_code": city.postal_code,
        "city": city.name,
        "country": "Deutschland",
        "country_code": "DE",
    }


def company_name(rng: random.Random, words: Sequence[str]) -> tuple[str, str, RegisterType, str | None]:
    """Returns (name_without_legal_form, legal_form, register_type, owner_surname_or_None)."""
    legal_form, _, register_type = rng.choices(
        ref.LEGAL_FORMS, weights=[lf.weight for lf in ref.LEGAL_FORMS], k=1)[0]
    word = rng.choice(words)
    surname: str | None = rng.choice(ref.SURNAMES)
    pattern = rng.randint(0, 3)
    if legal_form == "e.K.":
        pattern = rng.choice(EK_NAME_PATTERNS)
    if pattern == 0:
        base = f"{surname} {word}"
    elif pattern == 1:
        base = f"{surname} & {rng.choice(ref.SURNAMES)} {word}"
        surname = None
    elif pattern == 2:
        base = f"{rng.choice(ref.COMPANY_PREFIXES)}{rng.choice(ref.COMPANY_SUFFIXES)} {word}"
        surname = None
    else:
        base = f"{word} {surname}"
    return base, legal_form, register_type, surname


def build_vendor(rng: random.Random, index: int, used_names: set[str]) -> Vendor:
    industry: Industry = rng.choice(list(CATALOGS))
    while True:
        base, legal_form, register_type, owner_surname = company_name(rng, INDUSTRY_NAME_WORDS[industry])
        name = f"{base} {legal_form}"
        if name not in used_names:
            used_names.add(name)
            break

    city = rng.choice(ref.CITIES)
    area_code = city.area_code
    main_sub = subscriber_number(rng, area_code)
    phone_style = rng.choice(PHONE_STYLES)
    email_style = rng.choice(EMAIL_STYLES)
    domain = ascii_slug(base) + rng.choice((".de", ".de", ".de", "-gmbh.de" if "GmbH" in legal_form else ".com"))

    # Staff (one of them is the "Sachbearbeiter" on each quote)
    roles = ref.SALES_ROLES_BY_INDUSTRY.get(industry, ref.SALES_ROLES_DEFAULT)
    contacts: list[Person] = []
    used_ext: set[str] = set()
    for i in range(rng.randint(1, 4)):
        if legal_form == "e.K." and i == 0:
            p = make_person(rng, owner_surname)
            p.role = "Inhaber"
        else:
            p = make_person(rng)
            p.role = rng.choice(roles)
        ext = str(rng.randint(10, 99) if rng.random() < 0.7 else rng.randint(100, 399))
        while ext in used_ext:
            ext = str(int(ext) + 1)
        used_ext.add(ext)
        p.phone = format_phone(area_code, main_sub, ext, phone_style)
        p.mobile = mobile_number(rng, phone_style) if rng.random() < 0.3 else None
        p.email = f"{email_local_part(p.first_name, p.last_name, email_style)}@{domain}"
        contacts.append(p)

    mgmt_title = ref.MANAGEMENT_TITLES[legal_form]
    if legal_form == "e.K.":
        mgmt_names = [contacts[0].full_name]
    else:
        n = rng.randint(2, 3) if legal_form == "AG" else rng.randint(1, 2)
        mgmt_names = [make_person(rng).full_name for _ in range(n)]

    court = ref.REGISTER_COURT_OVERRIDES.get(city.name, f"Amtsgericht {city.name}")
    reg_number = (f"HRB {rng.randint(1000, 250000)}" if register_type == "HRB"
                  else f"HRA {rng.randint(100, 99999)}")
    bank_name = rng.choice(ref.BANK_NAMES).format(city=city.name.split(" (")[0])

    data: VendorData = {
        "name": name,
        "legal_form": legal_form,
        "address": make_address(rng, city),
        "phone": format_phone(area_code, main_sub, "0", phone_style),
        "fax": format_phone(area_code, main_sub, "99", phone_style) if rng.random() < 0.4 else None,
        "email": f"{rng.choice(CENTRAL_MAILBOXES)}@{domain}",
        "website": f"www.{domain}",
        "vat_id": vat_id_de(rng),
        "tax_number": tax_number(rng) if rng.random() < 0.35 else None,
        "commercial_register": {"court": court, "number": reg_number},
        "management": {"title": mgmt_title, "names": mgmt_names},
        "bank_account": {"bank_name": bank_name, "iban": iban_de(rng), "bic": bic(rng)},
    }

    # Keyword arguments are evaluated left to right: keep this order (see module docstring).
    style = VendorStyle(
        quote_number_format=rng.randint(0, 5),
        seq_base=rng.randint(100, 60000),
        customer_number_format=rng.randint(0, 4),
        customer_number_base=rng.randint(1000, 40000),
        customer_number_mult=rng.randint(1, 13),
        position_style=rng.choice(POSITION_STYLES_CONSTRUCTION if industry == "construction"
                                  else POSITION_STYLES_DEFAULT),
        unit_label_variant=rng.randint(0, 2),
        article_format=rng.randint(0, 3),
        article_prefix="".join(rng.choice(ARTICLE_PREFIX_LETTERS) for _ in range(rng.randint(1, 3))),
        show_article_numbers=(rng.random() < 0.8) and not industry == "construction",
        service_article_numbers=rng.random() < 0.3,
        price_style=rng.choice(PRICE_STYLES),
        validity_days=rng.choice(VALIDITY_DAYS),
        payment_terms=rng.randint(0, 6),
        delivery_terms=rng.choice(DELIVERY_TERMS_SITE if industry in SITE_INDUSTRIES else DELIVERY_TERMS_GOODS),
        free_shipping_threshold=rng.choice(FREE_SHIPPING_THRESHOLDS),
        line_discount_prob=rng.choice(LINE_DISCOUNT_PROBS),
        header_discount_prob=rng.choice(HEADER_DISCOUNT_PROBS),
        optional_position_prob=rng.choice(OPTIONAL_POSITION_PROBS),
        long_text_prob=rng.choice(LONG_TEXT_PROBS),
        intro_variant=rng.randint(0, 3),
        closing_variant=rng.randint(0, 3),
    )
    return Vendor(index, industry, data, contacts, style, area_code, main_sub)


def company_customer_name(rng: random.Random) -> tuple[str, str | None]:
    r = rng.random()
    if r < 0.08:
        return f"Steuerberatung {rng.choice(ref.SURNAMES)} & {rng.choice(ref.SURNAMES)} PartG mbB", "PartG mbB"
    if r < 0.14:
        return f"Gemeinschaftspraxis Dr. {rng.choice(ref.SURNAMES)} & Dr. {rng.choice(ref.SURNAMES)}", None
    base, legal_form, _, _ = company_name(rng, ref.CUSTOMER_INDUSTRY_WORDS)
    return f"{base} {legal_form}", legal_form


def build_customer(rng: random.Random, index: int) -> Customer:
    city = rng.choice(ref.CITIES)
    data: CustomerData
    if rng.random() < PRIVATE_CUSTOMER_SHARE:
        person = make_person(rng)
        data = {
            "type": "private",
            "name": person.full_name,
            "legal_form": None,
            "department": None,
            "person": {"salutation": person.salutation, "title": person.title,
                       "first_name": person.first_name, "last_name": person.last_name},
            "address": make_address(rng, city),
        }
        return Customer(index, data, [], person, city)

    name, legal_form = company_customer_name(rng)
    contacts: list[Person] = []
    for _ in range(rng.randint(0, 3)):
        p = make_person(rng)
        p.role = rng.choice(ref.CUSTOMER_ROLES)
        domain = ascii_slug(name.split(" ")[0] + " " + name.split(" ")[1]) + ".de"
        p.email = f"{email_local_part(p.first_name, p.last_name, 'first.last')}@{domain}" if rng.random() < 0.6 else None
        if rng.random() < 0.5:
            p.phone = format_phone(city.area_code, subscriber_number(rng, city.area_code),
                                   str(rng.randint(10, 999)), rng.choice(PHONE_STYLES))
        contacts.append(p)

    data = {
        "type": "company",
        "name": name,
        "legal_form": legal_form,
        "department": rng.choice(ref.CUSTOMER_DEPARTMENTS) if rng.random() < 0.35 else None,
        "person": None,
        "address": make_address(rng, city),
    }
    return Customer(index, data, contacts, None, city)


def build_world(seed: int) -> World:
    rng = random.Random(f"world:{seed}")
    used: set[str] = set()
    vendors = [build_vendor(rng, i, used) for i in range(NUM_VENDORS)]
    # Zipf-like popularity: a few vendors issue many quotes, most issue few.
    # Integer weights keep the draw independent of platform float rounding.
    weights = [1000 // (rank + 1) + 10 for rank in range(NUM_VENDORS)]
    customers = [build_customer(rng, i) for i in range(NUM_CUSTOMERS)]
    return World(seed, vendors, weights, customers)
