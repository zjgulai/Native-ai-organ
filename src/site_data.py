"""Content data loading for the Native AI Organ static site.

Single place that reads src/data/*.json and the figure manifests so the
rendering modules stay pure functions over plain dicts/lists.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"


def _load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


BOOK = _load("book.json")
BOOK2 = _load("book2.json")
BOOK3 = _load("book3.json")
CHAPTERS = _load("chapters-index.json")
CONCEPTS = _load("concepts.json")
TOOLS = _load("tools.json")
TERMS = _load("terms.json")
PILOT = _load("pilot.json")
PILOT_ASSETS = _load("pilot-assets.json")
BRAND_PLAN = _load("brand-plan.json")
ORGMAP = _load("orgmap.json")
SITEMAP = _load("sitemap.json")
SEMANTIC = _load("semantic.json")
SYNTHESIS = _load("synthesis.json")
TRILOGY = _load("triology.json")
FIG_SRC = json.loads((ROOT / "assets/figures/figures.json").read_text(encoding="utf-8"))
_manifest = ROOT / "assets/figures/manifest.json"
FIG_OUT = json.loads(_manifest.read_text(encoding="utf-8")) if _manifest.exists() else {}

CHAPTER_CONTENT: dict[str, dict] = {}
for f in sorted((DATA / "chapters").glob("*.json")):
    doc = json.loads(f.read_text(encoding="utf-8"))
    CHAPTER_CONTENT[doc["slug"]] = doc

BRAND2_CONTENT: dict[str, dict] = {}
for f in sorted((DATA / "brand2").glob("*.json")):
    doc = json.loads(f.read_text(encoding="utf-8"))
    BRAND2_CONTENT[doc["slug"]] = doc

# book2 chapters that have a published deep read, ordered by chapter number
BRAND2_DEEP = [c for c in BOOK2["chapters"] if c.get("deep") in BRAND2_CONTENT]

BOOK3_CONTENT: dict[str, dict] = {}
for f in sorted((DATA / "book3").glob("*.json")):
    doc = json.loads(f.read_text(encoding="utf-8"))
    BOOK3_CONTENT[doc["slug"]] = doc

BOOK3_DEEP = [c for c in BOOK3["chapters"] if c.get("deep") in BOOK3_CONTENT]

SITE_NAME = "Native AI Organ"
