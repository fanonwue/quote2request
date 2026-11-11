#!/usr/bin/env python3
"""Check that rendered PDFs still contain the ground truth of their JSON source.

Extracts the text layer of every PDF and looks for the key values (quote number, customer number,
references, VAT ID, every unit price / line total / tax amount / total, every position description).
Run it after changing a template:

    python generator/verify_pdf.py                       # generator/output/pdf vs generator/output
    python generator/verify_pdf.py --pdf /tmp/pdfs --in generator/output
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # works from any cwd, also with python -I

from pypdf import PdfReader

from pdfgen.render import money

DEFAULT_IN = Path(__file__).resolve().parent / "output"
WS = re.compile(r"\s+")


def expected_values(q: dict) -> list[str]:
    t = q["totals"]
    vals = [q["quote_number"], q["vendor"]["vat_id"], q["vendor"]["bank_account"]["bic"],
            q["vendor_contact"]["last_name"], q["customer"]["address"]["postal_code"],
            money(t["net_total"]), money(t["gross_total"])]
    vals += [x for x in (q["customer_number"], q["customer_reference"]) if x]
    vals += [money(x["amount"]) for x in t["tax"]]
    if t["discount"]:
        vals.append(money(t["discount"]["amount"]))
    if t["shipping"]:
        vals.append(money(t["shipping"]))
    for p in q["positions"]:
        vals += [money(p["unit_price"]), money(p["total_price"]), p["description"]]
        if p["article_number"]:
            vals.append(p["article_number"])
    return vals


def check(pdf: Path, q: dict) -> list[str]:
    # Compare without whitespace: line wrapping inside table cells splits words arbitrarily.
    text = WS.sub("", "".join(page.extract_text() for page in PdfReader(pdf).pages))
    return [v for v in expected_values(q) if WS.sub("", v) not in text]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", type=Path, default=DEFAULT_IN, help="directory with the quote_*.json files")
    ap.add_argument("--pdf", type=Path, help="directory with the PDFs (default: <in>/pdf)")
    args = ap.parse_args(argv)

    pdf_dir: Path = args.pdf or args.src / "pdf"
    pdfs = sorted(pdf_dir.glob("quote_*.pdf"))
    if not pdfs:
        ap.error(f"no quote_*.pdf in {pdf_dir}")

    failed = 0
    for pdf in pdfs:
        src = args.src / f"{pdf.stem}.json"
        if not src.exists():
            print(f"{pdf.name}: no source {src.name}")
            failed += 1
            continue
        missing = check(pdf, json.loads(src.read_text(encoding="utf-8")))
        if missing:
            failed += 1
            print(f"{pdf.name}: missing {len(missing)} value(s): {missing[:5]}")
    print(f"{len(pdfs) - failed}/{len(pdfs)} PDFs OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
