#!/usr/bin/env python3
"""Render generated quote JSON files into PDFs (one PDF per quote).

    pip install -r generator/requirements-pdf.txt
    python generator/render_pdf.py                         # all quotes in generator/output -> generator/output/pdf
    python generator/render_pdf.py --ids 1-20 --jobs 4     # a range, in parallel
    python generator/render_pdf.py --ids 7 --template lv   # force one template (ignores the vendor mapping)
    python generator/render_pdf.py --ids 7 --html          # also write the intermediate HTML (template debugging)
    python generator/render_pdf.py --list-templates

Each vendor is mapped to a template (and accent colour, logo style, ...) via a hash of its VAT ID,
so the same vendor always "sends" the same-looking PDF. A pdf_manifest.json records the template and
SHA-256 of every file.

The output directory is cleaned first: existing quote_*.pdf, quote_*.html and pdf_manifest.json are
deleted, so a run with --ids leaves only the selected PDFs.
"""

import argparse
import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # works from any cwd, also with python -I

from pdfgen import RENDERER_VERSION, DEFAULT_IN
from pdfgen.render import TEMPLATES, render_html, render_pdf


def parse_ids(spec: str) -> set[int]:
    ids: set[int] = set()
    for part in spec.split(","):
        a, _, b = part.strip().partition("-")
        ids.update(range(int(a), int(b or a) + 1))
    return ids


def render_one(job: tuple[Path, Path, str | None, bool]) -> dict:
    src, out_dir, template, write_html = job
    q = json.loads(src.read_text(encoding="utf-8"))
    r = render_pdf(q, template)
    target = out_dir / (src.stem + ".pdf")
    target.write_bytes(r.pdf)
    if write_html:
        html, _ = render_html(q, template)
        (out_dir / (src.stem + ".html")).write_text(html, encoding="utf-8")
    return {"id": q["id"], "file": target.name, "source": src.name, "template": r.identity.template,
            "vendor": q["vendor"]["name"], "pages": r.pages, "sha256": hashlib.sha256(r.pdf).hexdigest()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", type=Path, default=DEFAULT_IN, help=f"directory with quote_*.json (default: {DEFAULT_IN})")
    ap.add_argument("--out", type=Path, help="PDF output directory (default: <in>/../pdf)")
    ap.add_argument("--ids", help="only these quote ids, e.g. '1-20,42'")
    ap.add_argument("--template", choices=sorted(TEMPLATES), help="force a template for every quote")
    ap.add_argument("--jobs", type=int, default=1, help="parallel worker processes (default: 1)")
    ap.add_argument("--html", action="store_true", help="also write the rendered HTML next to each PDF")
    ap.add_argument("--list-templates", action="store_true", help="list templates and exit")
    args = ap.parse_args(argv)

    if args.list_templates:
        for name, desc in TEMPLATES.items():
            print(f"{name:10} {desc}")
        return 0

    sources = sorted(args.src.glob("quote_*.json"))
    if args.ids:
        wanted = parse_ids(args.ids)
        sources = [s for s in sources if int(s.stem.split("_")[1]) in wanted]
    if not sources:
        ap.error(f"no matching quote_*.json files in {args.src}")

    out: Path = args.out or args.src / ".." / "pdf"
    out.mkdir(parents=True, exist_ok=True)

    # Clear existing files
    for pattern in ("quote_*.pdf", "quote_*.html", "pdf_manifest.json"):
        for f in out.glob(pattern):
            f.unlink()

    print(f"Rendering {len(sources)} quotes to {out} using {args.jobs} jobs ...")

    jobs = [(s, out, args.template, args.html) for s in sources]

    if args.jobs > 1:
        with ProcessPoolExecutor(args.jobs) as pool:
            results = list(pool.map(render_one, jobs, chunksize=8))
    else:
        results = []
        for i, job in enumerate(jobs, 1):
            results.append(render_one(job))
            if i % 50 == 0:
                print(f"  {i}/{len(jobs)}", file=sys.stderr)

    manifest = {"renderer_version": RENDERER_VERSION, "forced_template": args.template,
                "count": len(results), "files": results}
    (out / "pdf_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    by_tpl: dict[str, int] = {}
    for r in results:
        by_tpl[r["template"]] = by_tpl.get(r["template"], 0) + 1
    print(f"Wrote {len(results)} PDFs to {out} ({', '.join(f'{k}: {n}' for k, n in sorted(by_tpl.items()))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
