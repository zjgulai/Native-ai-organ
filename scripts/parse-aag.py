#!/usr/bin/env python3
"""Parse cached ai-agent-guide chapter HTML into structured JSON.

Reads scripts/.cache/aag/*.html (produced by fetch-aag.py) and writes
scripts/.cache/aag-parse/{file}.json with heading tree + text blocks for
distillation. Stdlib only.

Run:  python3 scripts/fetch-aag.py && python3 scripts/parse-aag.py
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / ".cache" / "aag"
OUT = ROOT / "scripts" / ".cache" / "aag-parse"

SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside", "svg"}
BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "li", "pre", "blockquote", "td", "th"}


class ChapterParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.in_pre = False
        self.buf: list[str] = []
        self.blocks: list[dict] = []
        self.title = ""
        self._in_title = False

    def _flush(self, kind: str | None = None) -> None:
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        if not text:
            return
        self.blocks.append({"type": kind or "p", "text": text})

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in SKIP_TAGS:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "title":
            self._in_title = True
        if tag == "pre":
            self._flush()
            self.in_pre = True
            self.buf = []
            return
        if tag in BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1
            return
        if self.skip:
            return
        if tag == "title":
            self._in_title = False
            self.title = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            self.buf = []
            return
        if tag == "pre" and self.in_pre:
            text = "\n".join(line.rstrip() for line in "".join(self.buf).splitlines()).strip("\n")
            if text.strip():
                self.blocks.append({"type": "code", "text": text})
            self.buf = []
            self.in_pre = False
            return
        if tag in ("p", "h1", "h2", "h3", "h4", "li", "blockquote"):
            kind = {"h1": "h1", "h2": "h2", "h3": "h3", "h4": "h4",
                    "li": "li", "blockquote": "quote"}.get(tag, "p")
            self._flush(kind)
        elif tag == "td" or tag == "th":
            self._flush("cell")

    def handle_data(self, data: str) -> None:
        if self.skip or self._in_title:
            return
        self.buf.append(data)


def parse_file(path: Path) -> dict:
    p = ChapterParser()
    p.feed(path.read_text(encoding="utf-8", errors="replace"))
    p._flush()
    # merge consecutive cells into rough table rows is overkill; keep flat blocks
    heads = [b for b in p.blocks if b["type"] in ("h1", "h2", "h3", "h4")]
    return {
        "file": path.stem,
        "title": p.title,
        "headings": [h["text"] for h in heads],
        "blocks": p.blocks,
    }


def main() -> int:
    if not SRC.is_dir():
        print("No cache. Run scripts/fetch-aag.py first.", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(SRC.glob("*.html"))
    for f in files:
        doc = parse_file(f)
        (OUT / f"{f.stem}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        n = len(doc["blocks"])
        print(f"{f.stem}: {n} blocks, {len(doc['headings'])} headings")
    print(f"Parsed {len(files)} chapters -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
