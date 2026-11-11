"""Render generated quote JSON files into PDFs that look like they came from different vendors' systems.

Needs the optional dependencies in ``generator/requirements-pdf.txt`` (WeasyPrint, Jinja2).
The JSON generator (``quotegen``) itself stays pure standard library.

Bump RENDERER_VERSION whenever a template or helper change alters the rendered PDFs.
"""
from pathlib import Path
from typing import Final
from quotegen import DEFAULT_OUT

RENDERER_VERSION: Final[str] = "1.0.0"
DEFAULT_IN: Final[Path] = DEFAULT_OUT