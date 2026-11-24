#!/usr/bin/env python3
"""Build the Native AI Organ static reading site. Python stdlib only.

src/data/*.json  ->  dist/ static HTML + copied assets.
Run:  python3 build.py            # writes dist/
      python3 build.py --check    # build + verify links/assets
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import site_data as D  # noqa: E402
import site_pages as P  # noqa: E402

DIST = ROOT / "dist"


def write_page(rel: str, html: str) -> None:
    path = DIST / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def copy_assets() -> None:
    adir = DIST / "assets"
    adir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "src/styles.css", adir / "styles.css")
    shutil.copy2(ROOT / "src/site.js", adir / "site.js")
    fdir = adir / "figures"
    fdir.mkdir(exist_ok=True)
    for f in (ROOT / "assets/figures").glob("*.webp"):
        shutil.copy2(f, fdir / f.name)


def verify() -> list[str]:
    problems = []
    for hf in DIST.rglob("*.html"):
        html = hf.read_text(encoding="utf-8")
        for m in re.finditer(r'(?:href|src)="([^"#]+?)(?:#[^"]*)?"', html):
            url = m.group(1)
            if url.startswith(("http", "mailto:", "data:", "javascript:")):
                continue
            target = ((hf.parent / url) if not url.startswith("/")
                      else (DIST / url.lstrip("/"))).resolve()
            if not target.exists():
                problems.append(f"{hf.relative_to(DIST)}: broken link {url}")
    return problems


def build(check: bool = False) -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    write_page("index.html", P.render_home(""))
    write_page("about.html", P.render_about(""))
    write_page("terms.html", P.render_terms(""))
    write_page("pilot.html", P.render_pilot(""))
    write_page("pilot-assets.html", P.render_pilot_assets(""))
    write_page("brand-plan.html", P.render_brand_plan(""))
    write_page("orgmap.html", P.render_orgmap(""))
    write_page("product.html", P.render_product(""))
    write_page("semantic.html", P.render_semantic(""))
    write_page("sitemap.html", P.render_sitemap(""))
    write_page("synthesis.html", P.render_synthesis(""))
    write_page("triology.html", P.render_trilogy(""))
    write_page("chapters/index.html", P.render_chapters_index("../"))
    write_page("concepts/index.html", P.render_concepts("../"))
    write_page("tools/index.html", P.render_tools_index("../"))
    write_page("brand2/index.html", P.render_b2_index("../"))
    write_page("book3/index.html", P.render_b3_index("../"))
    for c in D.CHAPTERS:
        if c["slug"] in D.CHAPTER_CONTENT:
            write_page(f"chapters/{c['slug']}.html", P.render_chapter_page(c, "../"))
    for c in D.BRAND2_DEEP:
        write_page(f"brand2/{c['deep']}.html", P.render_b2_chapter_page(c["deep"], "../"))
    for c in D.BOOK3_DEEP:
        write_page(f"book3/{c['deep']}.html", P.render_b3_chapter_page(c["deep"], "../"))
    for t in D.TOOLS:
        write_page(f"tools/{t['slug']}.html", P.render_tool_page(t, "../"))

    copy_assets()

    n_html = len(list(DIST.rglob("*.html")))
    n_img = len(list((DIST / "assets/figures").glob("*.webp")))
    print(f"Built {n_html} pages, {n_img} figure images -> {DIST}")

    if check:
        problems = verify()
        if problems:
            print(f"\n{len(problems)} problems:")
            for p in problems[:30]:
                print(" -", p)
            return 1
        print("Link/asset verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(build(check="--check" in sys.argv))
