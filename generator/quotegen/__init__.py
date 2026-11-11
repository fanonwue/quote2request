"""Deterministic generator for synthetic (German) business quotes.

Bump GENERATOR_VERSION whenever a code change alters the generated output.
Same seed + same GENERATOR_VERSION => byte-identical output.
"""
from pathlib import Path
from typing import Final

GENERATOR_VERSION: Final[str] = "1.0.0"
SCHEMA_VERSION: Final[str] = "1.0"

DEFAULT_OUT: Final[Path] = Path(__file__).resolve().parent.parent / "output" / "json"