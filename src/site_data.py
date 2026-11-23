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
CHAPTERS = _load("chapters-index.json")
CONCEPTS = _load("concepts.json")
TOOLS = _load("tools.json")
FIG_SRC = json.loads((ROOT / "assets/figures/figures.json").read_text(encoding="utf-8"))
_manifest = ROOT / "assets/figures/manifest.json"
FIG_OUT = json.loads(_manifest.read_text(encoding="utf-8")) if _manifest.exists() else {}

CHAPTER_CONTENT: dict[str, dict] = {}
for f in sorted((DATA / "chapters").glob("*.json")):
    doc = json.loads(f.read_text(encoding="utf-8"))
    CHAPTER_CONTENT[doc["slug"]] = doc

SITE_NAME = "Native AI Organ"
