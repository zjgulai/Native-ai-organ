"""Rendering primitives: inline md-lite, content blocks, figures, page chrome.

All functions return HTML strings; data comes from site_data.
"""
from __future__ import annotations

import re
from html import escape

from site_data import BOOK, CHAPTERS, CHAPTER_CONTENT, CONCEPTS, TOOLS
from site_data import FIG_OUT, FIG_SRC, SITE_NAME

# ------------------------------------------------------------- inline md-lite

INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))")


def inline(text: str) -> str:
    """Escape HTML then apply **bold**, `code`, [text](href)."""
    out = escape(text, quote=False)

    def rep(m: re.Match) -> str:
        tok = m.group(0)
        if tok.startswith("**"):
            return "<strong>" + tok[2:-2] + "</strong>"
        if tok.startswith("`"):
            return "<code>" + tok[1:-1] + "</code>"
        mm = re.match(r"\[([^\]]+)\]\(([^)\s]+)\)", tok)
        if mm:
            return f'<a href="{escape(mm.group(2), quote=True)}">{mm.group(1)}</a>'
        return tok

    return INLINE_RE.sub(rep, out)


# ------------------------------------------------------------------ blocks

BLOCK_TAGS = {"p", "h2", "h3", "quote", "fig", "list", "olist", "table", "note", "map"}


def render_blocks(blocks: list, base: str, counters: dict, in_map: bool = False) -> str:
    out = []
    for b in blocks:
        kind = next(iter(b), None)
        if kind not in BLOCK_TAGS:
            raise ValueError(f"unknown block kind: {kind}")
        if kind == "p":
            out.append(f"<p>{inline(b['p'])}</p>")
        elif kind == "h2":
            if in_map:
                out.append(f'<h3 class="map-h">{escape(b["h2"])}</h3>')
                continue
            counters["h2"] += 1
            cid = f"sec-{counters['h2']}"
            counters["h3"] = 0
            out.append(f'<h2 id="{cid}"><span class="sec-no">{counters["h2"]:02d}</span>{escape(b["h2"])}</h2>')
        elif kind == "h3":
            if in_map:
                out.append(f'<h4 class="map-h4">{escape(b["h3"])}</h4>')
                continue
            counters["h3"] += 1
            cid = f"sec-{counters['h2']}-{counters['h3']}"
            out.append(f'<h3 id="{cid}">{escape(b["h3"])}</h3>')
        elif kind == "quote":
            cite = f'<footer>{escape(b["cite"])}</footer>' if b.get("cite") else ""
            out.append(f'<blockquote><span class="quote-mark">“</span>{inline(b["quote"])}{cite}</blockquote>')
        elif kind == "fig":
            out.append(render_figure(b["fig"], base))
        elif kind in ("list", "olist"):
            tag = "ol" if kind == "olist" else "ul"
            items = "".join(f"<li>{inline(i)}</li>" for i in b[kind])
            out.append(f"<{tag}>{items}</{tag}>")
        elif kind == "table":
            t = b["table"]
            head = "".join(f"<th>{inline(c)}</th>" for c in t["head"])
            rows = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>"
                for row in t["rows"]
            )
            out.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>')
        elif kind == "note":
            out.append(f'<div class="note">{inline(b["note"])}</div>')
        elif kind == "map":
            m = b["map"]
            inner = render_blocks(m["blocks"], base, {"h2": 0, "h3": 0}, in_map=True)
            out.append(
                '<section class="mapping" id="practice-mapping"><div class="map-head">'
                '<span class="tag">Practice Mapping</span>'
                f'<h2>{escape(m.get("title", "实践映射"))}</h2></div>'
                f'<div class="map-body">{inner}</div></section>'
            )
    return "".join(out)


def render_figure(fig_id: str, base: str) -> str:
    src = FIG_SRC.get(fig_id, {})
    out = FIG_OUT.get(fig_id, {})
    if out.get("status") != "ok" or not out.get("file"):
        return (f'<div class="note"><b>{escape(fig_id)}</b> 图像尚未导出'
                f'（原书第 {src.get("page", "?")} 页），内容以文字描述为准。</div>')
    caption = src.get("caption") or f"图 {fig_id.removeprefix('fig-')}"
    page = src.get("page", "?")
    src_label = f"摘自《AI Native 组织：从思考到实践》原书第 {page} 页"
    return (
        f'<figure class="figure"><a href="{base}assets/figures/{out["file"]}" target="_blank" rel="noopener">'
        f'<img src="{base}assets/figures/{out["file"]}" alt="{escape(caption)}" loading="lazy"></a>'
        f'<figcaption>{escape(caption)}<span class="src">{escape(src_label)} · '
        f'<a href="{base}assets/figures/{out["file"]}" target="_blank" rel="noopener">查看大图</a></span></figcaption></figure>'
    )


# ------------------------------------------------------------------ chrome


def nav_html(base: str, current: str) -> str:
    links = [
        ("index.html", "全书地图", "index"),
        ("chapters/index.html", "章节解读", "chapters"),
        ("concepts/index.html", "概念索引", "concepts"),
        ("pilot.html", "从书到试点", "pilot"),
        ("tools/index.html", "工具箱", "tools"),
        ("terms.html", "术语表", "terms"),
        ("about.html", "关于", "about"),
    ]
    items = "".join(
        f'<a href="{base}{href}"{" aria-current=\"page\"" if key == current else ""}>{label}</a>'
        for href, label, key in links
    )
    return (
        '<header class="nav"><a class="brand" href="' + base + 'index.html">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">'
        '<path d="M12 3 2.5 7.5 12 12l9.5-4.5L12 3Z"/><path d="M2.5 12 12 16.5 21.5 12"/>'
        '<path d="M2.5 16.5 12 21l9.5-4.5"/></svg>'
        f'{SITE_NAME}<small>BOOK NOTES</small></a>'
        f'<nav class="nav-links" id="nav-links" aria-label="主导航">{items}</nav>'
        '<button class="menu-toggle" aria-expanded="false" aria-controls="nav-links">菜单</button></header>'
    )


def sidebar_html(base: str, current_slug: str = "") -> str:
    """Left directory: search + grouped chapter list + concepts + tools."""
    groups = [("序章", "prologue"), ("上篇 · 道", "dao"), ("中篇 · 术", "shu"),
              ("下篇 · 器", "qi"), ("终章", "end")]
    out = ['<aside class="dir" aria-label="全书目录">',
           '<div class="dir-search"><label for="dir-search">搜索目录</label>',
           '<input id="dir-search" type="search" placeholder="章节、概念、工具…" autocomplete="off"></div>']
    for gname, key in groups:
        chs = [c for c in CHAPTERS if c.get("part_key") == key]
        if not chs:
            continue
        out.append(f'<div class="dir-group"><h4>{escape(gname)}</h4>')
        for c in chs:
            published = c["slug"] in CHAPTER_CONTENT
            if published:
                href = f'{base}chapters/{c["slug"]}.html'
                cur = ' aria-current="page"' if c["slug"] == current_slug else ""
                hay = f'{c["no"]} {c["title"]}'
                out.append(f'<a href="{href}"{cur} data-search="{escape(hay, quote=True)}">'
                           f'<span class="no">{c["no"]}</span>{escape(c["title"])}</a>')
            else:
                out.append(f'<a href="{base}chapters/index.html#pending-{c["slug"]}" data-search="{escape(c["no"]+" "+c["title"], quote=True)}">'
                           f'<span class="no">{c["no"]}</span>{escape(c["title"])}<span class="soon">撰写中</span></a>')
        out.append('</div>')
    out.append('<div class="dir-group"><h4>索引</h4>')
    out.append(f'<a href="{base}concepts/index.html" data-search="概念 索引 词条">概念索引（{len(CONCEPTS)}）</a>')
    out.append(f'<a href="{base}pilot.html" data-search="试点 品牌 跨境电商 操作序列 案例">从书到试点</a>')
    out.append(f'<a href="{base}tools/index.html" data-search="工具 附录 清单">随书工具（{len(TOOLS)}）</a>')
    out.append(f'<a href="{base}terms.html" data-search="术语 术语表 代号 决策">方案术语表</a>')
    out.append(f'<a href="{base}about.html" data-search="关于 版权 引用">关于与引用规范</a>')
    out.append('</div><p class="dir-empty" hidden>没有匹配的目录项。</p></aside>')
    return "".join(out)


def ptoc_html(headings: list[tuple[str, str]]) -> str:
    if not headings:
        return ""
    links = "".join(f'<a href="#{hid}">{escape(txt)}</a>' for hid, txt in headings)
    return (f'<aside class="ptoc" aria-label="本页内容"><strong>本页内容</strong><nav>{links}</nav>'
            '<p class="ptoc-note">深度解读 · 非原书转载。引用均标注原书页码。</p></aside>')


def page_shell(title: str, base: str, current: str, body: str,
               desc: str = "", head_extra: str = "") -> str:
    if not body.lstrip().startswith("<main"):
        body = f'<div class="wrap page-doc" style="padding:64px 0 90px">{body}</div>'
    return f"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{escape(desc, quote=True)}">
<title>{escape(title)} · {SITE_NAME}</title>
<link rel="stylesheet" href="{base}assets/styles.css">
{head_extra}</head><body>
{nav_html(base, current)}
{body}
<footer class="footer"><div class="wrap">
<div class="col"><h4>{SITE_NAME}</h4><p>《AI Native 组织：从思考到实践》深度解读笔记。个人精读库，内容为原创蒸馏与短引用，非原书转载。</p></div>
<div class="col"><h4>导航</h4><p><a href="{base}index.html">全书地图</a><br><a href="{base}chapters/index.html">章节解读</a><br><a href="{base}concepts/index.html">概念索引</a><br><a href="{base}pilot.html">从书到试点</a><br><a href="{base}tools/index.html">随书工具</a><br><a href="{base}terms.html">方案术语表</a><br><a href="{base}about.html">关于</a></p></div>
<div class="col"><h4>原书</h4><p>{escape(BOOK['title'])}<br>{escape(BOOK['author'])} 著 · {escape(BOOK['publisher'])} · {escape(BOOK['isbn'])}</p></div>
</div><div class="wrap legal">本站内容为读书笔记性质的 transformative use；图像裁自原书 PDF 供个人精读参考。引用规范见<a href="{base}about.html">关于页</a>。</div></footer>
<script src="{base}assets/site.js" defer></script>
</body></html>"""


def reader_page(base: str, current_slug: str, article_inner: str,
                headings: list, title: str, desc: str,
                nav_current: str = "chapters") -> str:
    body = (
        '<main class="reader">'
        '<button class="menu-toggle mobile-dir-btn" aria-expanded="false">目录</button>'
        + sidebar_html(base, current_slug)
        + f'<article class="article" id="article">{article_inner}</article>'
        + ptoc_html(headings)
        + '</main>'
    )
    return page_shell(title, base, nav_current, body, desc)
