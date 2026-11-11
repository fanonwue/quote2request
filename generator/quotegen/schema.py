"""Typed description of the generated JSON documents (quote files and manifest)."""

from typing import Literal, TypeAlias, TypedDict

Industry: TypeAlias = Literal["it", "industrial", "construction", "office", "electrical", "facility", "packaging"]
UnitKey: TypeAlias = Literal["piece", "hour", "meter", "sqm", "cbm", "kg", "liter", "lump", "set", "pack",
                           "carton", "roll", "pair", "month"]
Salutation: TypeAlias = Literal["Herr", "Frau"]
CustomerType: TypeAlias = Literal["company", "private"]
PositionType: TypeAlias = Literal["standard", "optional"]
DeliveryLabel: TypeAlias = Literal["Lieferanschrift", "Bauvorhaben", "Leistungsort", "Objekt"]
RegisterType: TypeAlias = Literal["HRB", "HRA"]


class Address(TypedDict):
    street: str
    house_number: str
    address_line2: str | None
    postal_code: str
    city: str
    country: str
    country_code: str


class PersonName(TypedDict):
    salutation: Salutation
    title: str | None
    first_name: str
    last_name: str


class PersonData(TypedDict):
    salutation: Salutation
    title: str | None
    first_name: str
    last_name: str
    role: str | None
    phone: str | None
    mobile: str | None
    email: str | None


class CommercialRegister(TypedDict):
    court: str
    number: str


class Management(TypedDict):
    title: str
    names: list[str]


class BankAccount(TypedDict):
    bank_name: str
    iban: str
    bic: str


class VendorData(TypedDict):
    name: str
    legal_form: str
    address: Address
    phone: str
    fax: str | None
    email: str
    website: str
    vat_id: str
    tax_number: str | None
    commercial_register: CommercialRegister
    management: Management
    bank_account: BankAccount


class CustomerData(TypedDict):
    type: CustomerType
    name: str
    legal_form: str | None
    department: str | None
    person: PersonName | None
    address: Address


class DeliveryAddress(TypedDict):
    label: DeliveryLabel
    name: str | None
    address: Address


class Unit(TypedDict):
    code: str
    label: str


class Position(TypedDict):
    position: str
    type: PositionType
    article_number: str | None
    description: str
    long_description: str | None
    quantity: str
    unit: Unit
    unit_price: str
    price_unit: int
    discount_percent: str | None
    tax_rate: str
    total_price: str


class HeaderDiscount(TypedDict):
    percent: str
    amount: str


class TaxLine(TypedDict):
    rate: str
    base: str
    amount: str


class Totals(TypedDict):
    positions_net: str
    discount: HeaderDiscount | None
    shipping: str | None
    net_total: str
    tax: list[TaxLine]
    tax_total: str
    gross_total: str


class PaymentTerms(TypedDict):
    net_days: int
    discount_days: int | None
    discount_percent: str | None
    text: str


class GeneratorInfo(TypedDict):
    version: str
    seed: int


class Quote(TypedDict):
    id: int
    schema_version: str
    generator: GeneratorInfo
    document_type: Literal["quote"]
    language: Literal["de"]
    currency: Literal["EUR"]
    quote_number: str
    quote_date: str
    valid_until: str
    subject: str | None
    customer_number: str | None
    customer_reference: str | None
    inquiry_date: str | None
    vendor: VendorData
    vendor_contact: PersonData
    customer: CustomerData
    customer_contact: PersonData | None
    delivery_address: DeliveryAddress | None
    intro_text: str
    positions: list[Position]
    totals: Totals
    payment_terms: PaymentTerms
    delivery_terms: str | None
    delivery_time: str
    closing_text: str


class ManifestEntry(TypedDict):
    id: int
    file: str
    sha256: str


class Manifest(TypedDict):
    generator_version: str
    schema_version: str
    seed: int
    start_id: int
    count: int
    files: list[ManifestEntry]
