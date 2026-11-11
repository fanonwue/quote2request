"""Identifiers with real check digits (USt-IdNr., IBAN) and contact formatting helpers."""

import random
import string
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Final, Literal, TypeAlias

from . import reference_data as ref

PhoneStyle: TypeAlias = Literal["intl", "national", "slash"]
EmailStyle: TypeAlias = Literal["first.last", "f.last", "last", "firstlast"]

PHONE_STYLES: Final[tuple[PhoneStyle, ...]] = ("intl", "national", "slash")
EMAIL_STYLES: Final[tuple[EmailStyle, ...]] = ("first.last", "f.last", "last", "firstlast")

BIC_LOCATIONS: Final[tuple[str, ...]] = ("FF", "MM", "HH", "BB", "DD", "SS", "2H", "33", "M1")
BIC_BRANCHES: Final[tuple[str, ...]] = ("XXX", "", "XXX")

# Subscriber number length by area-code length (incl. leading 0)
SUBSCRIBER_LENGTHS: Final[Mapping[int, int]] = {3: 8, 4: 7, 5: 6}

TRANSLITERATIONS: Final[tuple[tuple[str, str], ...]] = (
    ("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"),
    ("Ü", "Ue"), ("ß", "ss"), ("ı", "i"), ("&", " "),
)


def vat_id_de(rng: random.Random) -> str:
    """German USt-IdNr. (DE + 9 digits) with a valid ISO 7064 MOD 11,10 check digit."""
    digits = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(7)]
    return "DE" + "".join(map(str, digits)) + str(vat_id_check_digit(digits))


def vat_id_check_digit(digits: Sequence[int]) -> int:
    product = 10
    for d in digits:
        s = (d + product) % 10
        if s == 0:
            s = 10
        product = (2 * s) % 11
    check = 11 - product
    return 0 if check == 10 else check


def iban_de(rng: random.Random) -> str:
    """German IBAN (electronic format, no spaces) with valid mod-97 check digits."""
    blz = str(rng.randint(1, 8)) + "".join(str(rng.randint(0, 9)) for _ in range(7))
    account = "".join(str(rng.randint(0, 9)) for _ in range(10))
    bban = blz + account
    check = 98 - int(bban + "131400") % 97  # "DE" -> 13 14, check digits "00"
    return f"DE{check:02d}{bban}"


def bic(rng: random.Random) -> str:
    bank = "".join(rng.choice(string.ascii_uppercase) for _ in range(4))
    location = rng.choice(BIC_LOCATIONS)
    branch = rng.choice(BIC_BRANCHES)
    return f"{bank}DE{location}{branch}"


def tax_number(rng: random.Random) -> str:
    return f"{rng.randint(10, 99)}/{rng.randint(100, 999)}/{rng.randint(10000, 99999)}"


def ascii_slug(text: str, sep: str = "-") -> str:
    for a, b in TRANSLITERATIONS:
        text = text.replace(a, b)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    words: list[str] = []
    cur = ""
    for c in text:
        if c.isascii() and c.isalnum():
            cur += c
        elif cur:
            words.append(cur)
            cur = ""
    if cur:
        words.append(cur)
    return sep.join(words)


def subscriber_number(rng: random.Random, area_code: str) -> str:
    length = SUBSCRIBER_LENGTHS.get(len(area_code), 7) - rng.randint(0, 1)
    return str(rng.randint(2, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(length - 1))


def format_phone(area_code: str, subscriber: str, extension: str | None, style: PhoneStyle) -> str:
    ext = f"-{extension}" if extension else ""
    if style == "intl":
        return f"+49 {area_code[1:]} {subscriber}{ext}"
    if style == "slash":
        return f"{area_code}/{subscriber}{ext}"
    return f"{area_code} {subscriber}{ext}"


def mobile_number(rng: random.Random, style: PhoneStyle) -> str:
    prefix = rng.choice(ref.MOBILE_PREFIXES)
    number = "".join(str(rng.randint(0, 9)) for _ in range(rng.choice((7, 8))))
    if style == "intl":
        return f"+49 {prefix} {number}"
    return f"0{prefix} {number}"


def email_local_part(first: str, last: str, style: EmailStyle) -> str:
    f, l = ascii_slug(first, ""), ascii_slug(last, "")
    if style == "first.last":
        return f"{f}.{l}"
    if style == "f.last":
        return f"{f[0]}.{l}"
    if style == "last":
        return l
    return f"{f}{l}"
