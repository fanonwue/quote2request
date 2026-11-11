# Quote test-data generator

Generates synthetic, reproducible German business quotes (*Angebote*) as JSON, one file per quote.
Pure Python standard library (3.10+), with no runtime dependencies. Fully type-annotated and checked
with `mypy --strict` (see `mypy.ini`). The JSON structure is defined as TypedDicts in `quotegen/schema.py`.

```bash
python generator/generate.py                       # 1000 quotes, seed 42 -> generator/output/
python generator/generate.py --count 10000         # more data
python generator/generate.py --seed 7 --out /tmp/q # different dataset
python generator/verify.py                         # check arithmetic, checksums, reproducibility
pip install -r generator/requirements-dev.txt      # once
(cd generator && mypy generate.py verify.py quotegen)   # type check
```

The output directory is cleaned first (old `quote_*.json` and `manifest.json` are deleted).

Output: `output/quote_000001.json` … plus `output/manifest.json` (seed, version, SHA-256 per file).

## Reproducibility

* Each quote gets its own RNG seeded from `(seed, id)`. Quote *N* is byte-identical whether you
  generate 10 or 10,000 quotes, or only a range (`--start-id 500 --count 20`).
* Vendors (60) and customers (500) form a fixed "world" per seed. A vendor always has the same
  letterhead, staff, numbering scheme, unit labels and article numbers across all its quotes.
* No wall-clock time, no `hash()`, no set iteration, no `log`/`pow` in random draws. Money is
  `Decimal` with integer-cent draws.
* The order of RNG calls defines the output. Reordering draws, even within a dict literal or
  constructor call, changes every file.
* Guarantee: same `seed` + same `GENERATOR_VERSION` (in `quotegen/__init__.py`) ⇒ identical
  bytes. **Bump the version whenever you change the output.**
* `verify.py` regenerates every file and compares it byte for byte, checks the manifest hashes, and
  recomputes all totals independently.

## Data model

Numbers that represent money, quantities or percentages are **JSON strings** (`"1450.31"`,
`"2.5"`, `"19.00"`) so they stay exact. Dates are ISO `YYYY-MM-DD`. Absent values are `null`.

| Field | German term | Notes |
|---|---|---|
| `id` | – | Sequential dataset ID, same as file name |
| `quote_number` | Angebotsnummer | Vendor-specific format (`AN-2025-01234`, `ANG25012345`, …) |
| `quote_date`, `valid_until` | Angebotsdatum, gültig bis | |
| `subject` | Betreff / Bauvorhaben | |
| `customer_number` | Kundennummer | `null` for prospects |
| `customer_reference`, `inquiry_date` | Ihre Anfrage / Ihr Zeichen | |
| `vendor` | Anbieter | Address, phone/fax/email/web, `vat_id` (USt-IdNr., valid check digit), `tax_number` (Steuernummer), `commercial_register` (Registergericht + HRB/HRA), `management` (Geschäftsführer/Vorstand/Inhaber), `bank_account` (IBAN with valid check digits, BIC) |
| `vendor_contact` | **Sachbearbeiter** / Ansprechpartner | English: *contact person* / *person in charge*. Name, role, direct phone, email |
| `customer` | Kunde | `type` = `company` or `private`; company name + department, or a person |
| `customer_contact` | Ansprechpartner beim Kunden | Drives the salutation in `intro_text` |
| `delivery_address` | Lieferanschrift / Bauvorhaben / Objekt | `label` says which; `null` = same as customer address |
| `positions[]` | Positionen | see below |
| `totals` | Summen | `positions_net`, header `discount`, `shipping`, `net_total`, `tax[]` per rate (`rate`, `base`, `amount`), `tax_total`, `gross_total` |
| `payment_terms` | Zahlungsbedingungen | `net_days`, Skonto (`discount_days`, `discount_percent`), printed `text` |
| `delivery_terms`, `delivery_time` | Lieferbedingungen, Lieferzeit | |
| `intro_text`, `closing_text` | Anschreiben / Schlusstext | |

**Position fields:** `position` (printed label: `1`, `10`, `001`, `01.0010`), `type`
(`standard` | `optional`, i.e. Bedarfs-/Eventualposition), `article_number`, `description`,
`long_description`, `quantity` (Menge), `unit` (`code` = UN/ECE Rec. 20 such as `H87`/`HUR`/`MTK`,
`label` = as printed, e.g. `Stk.`/`Stück`/`St.`), `unit_price` (Einzelpreis), `price_unit`
(Preiseinheit, e.g. `100` = price per 100 pieces), `discount_percent` (Rabatt), `tax_rate`,
`total_price` (Gesamtpreis, net).

### Arithmetic (rounded half-up to cents)

```
total_price         = round(quantity × unit_price / price_unit × (1 − discount_percent/100))
per tax rate r:       discount_r = round(Σ standard lines at r × header_discount/100)
                      base_r     = Σ lines at r − discount_r  (+ shipping, if r = 19 %)
                      tax_r      = round(base_r × r/100)
net_total           = positions_net − discount + shipping
gross_total         = net_total + Σ tax_r
```
Optional positions are priced but **not** included in the totals.

## Content

7 vendor industries with their own catalogs: IT, industrial supplies, construction/finishing,
office supplies, electrical, facility services, packaging. They mix 19 % and 7 % VAT,
per-100 pricing, hours, m², lump sums, monthly fees, line and header discounts, Skonto, and
shipping based on free-shipping thresholds. All names, addresses, phone numbers, VAT IDs and IBANs
are fictional. The check digits are valid, so they pass format validation.

## PDF rendering

`render_pdf.py` turns the JSON files into PDFs that look like they came from different vendors'
systems. The output directory is cleaned first (old `quote_*.pdf`, `quote_*.html`, `pdf_manifest.json` are
deleted), so `--ids` leaves only the selected PDFs. It is optional and has its own dependencies (WeasyPrint needs Pango from the OS):

```bash
pip install -r generator/requirements-pdf.txt
python generator/render_pdf.py --jobs 8                # all quotes -> generator/output/pdf/
python generator/render_pdf.py --ids 1-20,42           # a subset
python generator/render_pdf.py --template lv --out /tmp/lv   # force one template
python generator/render_pdf.py --ids 7 --html          # also dump the HTML (template debugging)
python generator/verify_pdf.py                         # PDFs still contain all key JSON values?
```

| Template | Looks like | Distinguishing features |
|---|---|---|
| `din5008` | Classic business letter | DIN 5008 form B geometry (window, fold/hole marks), info block, 4-column footer |
| `modern` | Online invoicing tool | Lato, accent colour, zebra table, article no. under the description, "Optional" badge |
| `erp` | ERP printout | Monospace, ruled header grid, `PE` price-unit column, tax codes (`St 1/2`), `*` for optional lines |
| `lv` | Tradesman / construction (Leistungsverzeichnis) | Serif, OZ/EP/GP, facts line, acceptance slip with signature lines |

* **Per-vendor identity.** A SHA-256 of the vendor's VAT ID picks the template, accent colour, logo
  style (monogram circle/square/bar or plain text), long or short letter date, and `€` vs `EUR`. A
  vendor always looks the same, and the PDF metadata (`Creator`, `Author`, `Title`, creation date =
  quote date) matches it.
* **Same content, different layout.** Labels, column sets and formats change between templates
  (`Menge 2,5` / `2,500` / `2,50`, `4,71 / 100 St.` / `PE 100`, `Gesamtbetrag` / `Endbetrag EUR` /
  `Angebotssumme brutto`). Columns for discount, VAT rate and article number appear only when needed.
* **Ground truth stays complete.** Every value an extractor should find is printed. Optional
  positions show their total too, marked as excluded from the sum. `verify_pdf.py` checks this on the
  PDF text layer.
* **Reproducible.** Fixed PDF identifier and metadata dates, so the same input on the same machine
  gives byte-identical PDFs. Output also depends on the WeasyPrint version and installed fonts. Font
  stacks prefer Arial/Courier New/Georgia and fall back to Liberation/DejaVu. `pdf_manifest.json`
  records the template, page count and SHA-256 of each file.
* Bump `RENDERER_VERSION` in `pdfgen/__init__.py` when a template change alters the output.

Templates live in `pdfgen/templates/` (`<name>.html.j2` + `<name>.css.j2`, shared `_base`/`_macros`).
To add one, create both files, register it in `TEMPLATES` in `pdfgen/render.py`, and check the result
with `verify_pdf.py`. Adding a template changes the vendor-to-template mapping.

## Layout

```
generate.py              CLI, serialization, manifest
verify.py                independent checks + regeneration comparison
quotegen/schema.py       TypedDicts for the JSON output (Quote, Position, Totals, Manifest, ...)
quotegen/reference_data  names, cities (PLZ + area code), streets, legal forms
quotegen/catalog.py      units of measure, items per industry, subjects
quotegen/identifiers.py  USt-IdNr., IBAN, BIC, phone/email formatting
quotegen/parties.py      vendor/customer "world"
quotegen/quote.py        quote assembly and totals
render_pdf.py            CLI: JSON -> PDF, pdf_manifest.json
verify_pdf.py            checks rendered PDFs against their JSON
pdfgen/render.py         vendor identity, formatting filters, Jinja2 + WeasyPrint
pdfgen/templates/        din5008, modern, erp, lv (HTML + CSS templates)
```
