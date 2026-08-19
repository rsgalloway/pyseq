"""Minimal Sphinx configuration for pyseq API docs and intersphinx inventory."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "lib"

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

import pyseq


project = "pyseq"
author = "Ryan Galloway"
copyright = "2011-2026, Ryan Galloway"
version = pyseq.__version__
release = pyseq.__version__

extensions = [
    "sphinx.ext.autodoc",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

autodoc_member_order = "bysource"

html_theme = "alabaster"
html_theme_options = {
    "description": "Python library for numbered file sequences",
    "fixed_sidebar": True,
    "page_width": "1180px",
    "sidebar_width": "280px",
}
html_title = f"pyseq {release} API"
html_show_sourcelink = False
html_copy_source = False
html_static_path = ["_static"]
html_css_files = ["custom.css"]

