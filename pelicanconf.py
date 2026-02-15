from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "_python"))

try:
    from filters import filters as urubu_filters
except Exception:
    urubu_filters = {}

AUTHOR = "Occasional Prayers"
SITENAME = "Occasional Prayers"
SITEURL = ""
TIMEZONE = "UTC"
DEFAULT_LANG = "en"

PATH = "."
OUTPUT_PATH = "_build_pelican"
THEME = "themes/occasional-prayers"

ARTICLE_PATHS: list[str] = []
PAGE_PATHS = [
    "index-pelican.md",
    "about.md",
    "404.md",
    "search.md",
    "notfound.md",
    "acna2019",
    "acna2019collects",
    "coe1662",
    "coi2004",
    "davidtaylor",
    "other",
    "parish-devotional",
    "parish-intercessory",
    "parish-occasions",
    "parish-sacraments",
    "parish-supplementary",
    "parish-year",
    "potec",
    "tag",
    "tec1928",
    "tec1979",
]
PAGE_EXCLUDES: list[str] = []
IGNORE_FILES = ["**/.DS_Store", "AGENTS.md", "README.md", "TODO.md"]
PATH_METADATA = r"(?P<path>.*)\.md"

STATIC_PATHS = ["css", "images", "js", "manifest.json"]
EXTRA_PATH_METADATA = {
    "manifest.json": {"path": "manifest.json"},
}

DIRECT_TEMPLATES: list[str] = []
PAGINATED_TEMPLATES: dict[str, str] = {}

PAGE_URL = "{path}.html"
PAGE_SAVE_AS = "{path}.html"

JINJA_FILTERS = urubu_filters
PLUGIN_PATHS = ["_python"]
PLUGINS = ["pelican_compat"]

# Keep parity-focused output while migration is in progress.
DEFAULT_PAGINATION = False
RELATIVE_URLS = False
