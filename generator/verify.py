#!/usr/bin/env python3
"""Verify generated quotes.

Checks, per file:
  * sha256 matches manifest.json
  * byte-identical to a fresh regeneration with the manifest's seed (reproducibility)
  * arithmetic: line totals, discounts, tax per rate, net/gross totals (recomputed independently)
  * consistency: id vs file name, dates, IBAN / USt-IdNr. check digits, unique quote numbers per vendor

    python generator/verify.py [--out generator/output] [--no-regen]
"""

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Final, cast, get_args

sys.path.insert(0, str(Path(__file__).resolve().parent))  # works from any cwd, also with python -I

from generate import generate
from quotegen.schema import Manifest, PositionType, Quote

DEFAULT_OUT: Final[Path] = Path(__file__).resolve().parent / "output"


def r2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def iban_ok(iban: str) -> bool:
    s = iban[4:] + iban[:4]
    digits = "".join(str(int(c, 36)) for c in s)
    return int(digits) % 97 == 1


def vat_ok(vat: str) -> bool:
    if not (vat.startswith("DE") and len(vat) == 11 and vat[2:].isdigit()):
        return False
    product = 10
    for c in vat[2:10]:
        s = (int(c) + product) % 10 or 10
        product = (2 * s) % 11
    check = (11 - product) % 10
    return check == int(vat[10])


def check_quote(q: Quote) -> list[str]:
    errs: list[str] = []
    D = Decimal

    # Positions
    by_rate: dict[Decimal, Decimal] = {}
    for p in q["positions"]:
        qty, price, pu = D(p["quantity"]), D(p["unit_price"]), D(p["price_unit"])
        disc = D(p["discount_percent"]) if p["discount_percent"] else D(0)
        expected = r2(qty * price / pu * (1 - disc / 100))
        if expected != D(p["total_price"]):
            errs.append(f"pos {p['position']}: total {p['total_price']} != {expected}")
        # The file is untrusted JSON: the Literal type is only a claim, so check it at runtime.
        if p["type"] not in get_args(PositionType):
            errs.append(f"pos {p['position']}: unknown type {p['type']}")
        elif p["type"] == "standard":
            by_rate[D(p["tax_rate"])] = by_rate.get(D(p["tax_rate"]), D(0)) + D(p["total_price"])

    t = q["totals"]
    positions_net = sum(by_rate.values(), D(0))
    if positions_net != D(t["positions_net"]):
        errs.append(f"positions_net {t['positions_net']} != {positions_net}")

    pct = D(t["discount"]["percent"]) if t["discount"] else D(0)
    bases: dict[Decimal, Decimal] = {}
    disc_total = D(0)
    for rate, amount in by_rate.items():
        d = r2(amount * pct / 100)
        disc_total += d
        bases[rate] = amount - d
    if t["discount"] and D(t["discount"]["amount"]) != disc_total:
        errs.append(f"discount {t['discount']['amount']} != {disc_total}")
    shipping = D(t["shipping"]) if t["shipping"] else D(0)
    if shipping:
        bases[D(19)] = bases.get(D(19), D(0)) + shipping

    reported = {D(x["rate"]): x for x in t["tax"]}
    if set(reported) != set(bases):
        errs.append(f"tax rates {sorted(reported)} != {sorted(bases)}")
    tax_total = D(0)
    for rate, base in bases.items():
        amount = r2(base * rate / 100)
        tax_total += amount
        x = reported.get(rate)
        if x and (D(x["base"]) != base or D(x["amount"]) != amount):
            errs.append(f"tax {rate}%: {x} != base {base} amount {amount}")

    net = positions_net - disc_total + shipping
    if D(t["net_total"]) != net:
        errs.append(f"net_total {t['net_total']} != {net}")
    if D(t["tax_total"]) != tax_total:
        errs.append(f"tax_total {t['tax_total']} != {tax_total}")
    if D(t["gross_total"]) != net + tax_total:
        errs.append(f"gross_total {t['gross_total']} != {net + tax_total}")

    # Consistency
    qd, vu = date.fromisoformat(q["quote_date"]), date.fromisoformat(q["valid_until"])
    if vu <= qd:
        errs.append("valid_until not after quote_date")
    if q["inquiry_date"] and date.fromisoformat(q["inquiry_date"]) >= qd:
        errs.append("inquiry_date not before quote_date")
    if not iban_ok(q["vendor"]["bank_account"]["iban"]):
        errs.append("invalid IBAN")
    if not vat_ok(q["vendor"]["vat_id"]):
        errs.append("invalid USt-IdNr.")
    if not q["positions"]:
        errs.append("no positions")
    return errs


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--no-regen", action="store_true", help="skip the regeneration (reproducibility) check")
    args = ap.parse_args(argv)

    out: Path = args.out
    no_regen: bool = args.no_regen
    manifest = cast(Manifest, json.loads((out / "manifest.json").read_text(encoding="utf-8")))
    regenerated: dict[int, bytes] = {}
    if not no_regen:
        regenerated = dict(generate(manifest["seed"], manifest["start_id"], manifest["count"]))

    failures = 0
    quote_numbers: dict[tuple[str, str], int] = {}
    for entry in manifest["files"]:
        path = out / entry["file"]
        data = path.read_bytes()
        errs: list[str] = []
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            errs.append("sha256 mismatch with manifest")
        if regenerated and regenerated.get(entry["id"]) != data:
            errs.append("differs from fresh regeneration")
        q = cast(Quote, json.loads(data))
        if q["id"] != entry["id"]:
            errs.append(f"id {q['id']} != manifest id {entry['id']}")
        key = (q["vendor"]["name"], q["quote_number"])
        if key in quote_numbers:
            errs.append(f"duplicate quote number {key} (also id {quote_numbers[key]})")
        quote_numbers[key] = q["id"]
        errs += check_quote(q)
        if errs:
            failures += 1
            print(f"{entry['file']}:")
            for e in errs:
                print(f"  - {e}")

    n = len(manifest["files"])
    print(f"{n - failures}/{n} quotes OK" + ("" if regenerated else " (regeneration check skipped)"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
