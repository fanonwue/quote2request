#!/usr/bin/env python3
"""Generate reproducible synthetic quotes as one JSON file per quote.

The output directory is cleaned first: existing quote_*.json and manifest.json are deleted.

    python generator/generate.py                       # 1000 quotes, seed 42 -> generator/output/
    python generator/generate.py --count 5000 --seed 7 --out /tmp/quotes
"""

import argparse
import hashlib
import json
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # works from any cwd, also with python -I

from quotegen import GENERATOR_VERSION, SCHEMA_VERSION, DEFAULT_OUT
from quotegen.parties import build_world
from quotegen.quote import build_quote
from quotegen.schema import Manifest, ManifestEntry, Quote


def file_name(quote_id: int) -> str:
    return f"quote_{quote_id:06d}.json"


def serialize(doc: Quote | Manifest) -> bytes:
    """Canonical serialization: stable key order (insertion order), UTF-8, LF, trailing newline."""
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def generate(seed: int, start_id: int, count: int) -> Iterator[tuple[int, bytes]]:
    """Yield (id, bytes) for each quote."""
    world = build_world(seed)
    for quote_id in range(start_id, start_id + count):
        yield quote_id, serialize(build_quote(world, quote_id))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--count", type=int, default=1000, help="number of quotes (default: 1000)")
    ap.add_argument("--seed", type=int, default=42, help="master seed (default: 42)")
    ap.add_argument("--start-id", type=int, default=1, help="first quote id (default: 1)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output directory (default: {DEFAULT_OUT})")
    args = ap.parse_args(argv)
    out: Path = args.out
    seed: int = args.seed
    start_id: int = args.start_id
    count: int = args.count

    if count < 1 or start_id < 1:
        ap.error("--count and --start-id must be >= 1")

    out.mkdir(parents=True, exist_ok=True)

    # Clear existing files
    for pattern in ("quote_*.json", "manifest.json"):
        for f in out.glob(pattern):
            f.unlink()

    files: list[ManifestEntry] = []
    for quote_id, data in generate(seed, start_id, count):
        name = file_name(quote_id)
        (out / name).write_bytes(data)
        files.append({"id": quote_id, "file": name, "sha256": hashlib.sha256(data).hexdigest()})

    manifest: Manifest = {
        "generator_version": GENERATOR_VERSION,
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "start_id": start_id,
        "count": count,
        "files": files,
    }
    (out / "manifest.json").write_bytes(serialize(manifest))

    print(f"Wrote {len(files)} quotes (seed={seed}) to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
