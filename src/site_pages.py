"""Page-level renderers: home, chapter, chapters index, concepts, tools, about."""
import json
import re
from html import escape

from site_data import (BOOK, BOOK2, BOOK3, BOOK4, AGENT_LAB, STACK, BRAND2_CONTENT, BRAND2_DEEP,
                       BRAND_PLAN, CHAPTERS, CHAPTER_CONTENT, CONCEPTS,
                       ORGMAP, SITEMAP, SEMANTIC, G1_PACK, TOOLS, TERMS, PILOT, PILOT_ASSETS,
                       PRODUCT, EXPERIMENTS, TOYAGENT_STEPS,
                       SYNTHESIS, TRILOGY, FIG_SRC, SITE_NAME, BOOK3_CONTENT, BOOK3_DEEP,
                       BOOK4_CONTENT, BOOK4_DEEP, AGENT_PLAYBOOK, AGENT_PLAYBOOK_CONTENT,
                       AGENT_PLAYBOOK_NODES)
from site_render import (inline, render_blocks, page_shell, reader_page,
                         sidebar_html_b2, sidebar_html_b3, sidebar_html_b4,
                         sidebar_html_pb)


def chapter_headings(blocks: list) -> list[tuple[str, str]]:
    heads = []
    counters = {"h2": 0, "h3": 0}
    for b in blocks:
        if "h2" in b:
            counters["h2"] += 1
            counters["h3"] = 0
            heads.append((f"sec-{counters['h2']}", b["h2"]))
        elif "h3" in b:
            counters["h3"] += 1
            heads.append((f"sec-{counters['h2']}-{counters['h3']}", b["h3"]))
        elif "map" in b:
            heads.append(("practice-mapping", b["map"].get("title", "实践映射")))
    return heads


def render_chapter_page(c: dict, base: str) -> str:
    doc = CHAPTER_CONTENT[c["slug"]]
    blocks = doc["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    idx = next(i for i, x in enumerate(CHAPTERS) if x["slug"] == c["slug"])
    prev_c = next((CHAPTERS[j] for j in range(idx - 1, -1, -1)
                   if CHAPTERS[j]["slug"] in CHAPTER_CONTENT), None)
    next_c = next((CHAPTERS[j] for j in range(idx + 1, len(CHAPTERS))
                   if CHAPTERS[j]["slug"] in CHAPTER_CONTENT), None)
    pager = '<nav class="pager">'
    pager += (f'<a href="{base}chapters/{prev_c["slug"]}.html"><span class="dir-label">← 上一章</span>'
              f'<span class="ttl">第 {prev_c["no"]} 章 · {escape(prev_c["title"])}</span></a>' if prev_c
              else '<span></span>')
    pager += (f'<a class="next" href="{base}chapters/{next_c["slug"]}.html"><span class="dir-label">下一章 →</span>'
              f'<span class="ttl">第 {next_c["no"]} 章 · {escape(next_c["title"])}</span></a>' if next_c
              else '<span></span>')
    pager += '</nav>'
    figs = sum(1 for b in blocks if "fig" in b)
    inner = (
        f'<div class="crumb"><a href="{base}index.html">全书地图</a><span>/</span>'
        f'<a href="{base}chapters/index.html">章节解读</a><span>/</span>'
        f'<span>第 {c["no"]} 章</span></div>'
        f'<div class="cat">{escape(c.get("part_name", ""))} · 第 {c["no"]} 章</div>'
        f'<h1>{escape(c["title"])}</h1>'
        f'<p class="lead">{inline(doc.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>原书页码 <b>{escape(c.get("pages", "—"))}</b></span>'
        f'<span>约 <b>{c.get("minutes", "—")}</b> 分钟读完</span>'
        f'<span>收录插图 <b>{figs}</b> 幅</span>'
        '<span>状态 <b>深度解读已发布</b></span></div></div>'
        + body_html + pager
    )
    title = f'第{c["no"]}章 {c["title"]}'
    return reader_page(base, c["slug"], inner, heads, title,
                       doc.get("lead", "")[:120])


def render_chapters_index(base: str) -> str:
    rows = []
    for c in CHAPTERS:
        pub = c["slug"] in CHAPTER_CONTENT
        if pub:
            doc = CHAPTER_CONTENT[c["slug"]]
            rows.append(
                f'<div class="ch-item live" id="ch-{c["slug"]}">'
                f'<span class="no">{c["no"]}</span>'
                f'<span class="t"><a href="{base}chapters/{c["slug"]}.html">{escape(c["title"])}</a>'
                f'<small>{escape(doc.get("lead", ""))[:80]}…</small></span>'
                f'<span class="st">已发布 · {c.get("pages", "—")}页</span></div>')
        else:
            rows.append(
                f'<div class="ch-item" id="pending-{c["slug"]}">'
                f'<span class="no">{c["no"]}</span>'
                f'<span class="t">{escape(c["title"])}<small>{escape(c.get("part_name", ""))}</small></span>'
                f'<span class="st"><span class="soon">撰写中</span></span></div>')
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span><span>章节解读</span></div>'
        '<div class="cat">CHAPTERS</div><h1>章节解读</h1>'
        '<p class="sub">十三章正文 + 序章与终章，共 15 篇，按「道—术—器」三篇组织。每篇为原创深度解读：核心论点蒸馏、书中插图、短引用（标注页码），并附「实践映射」。</p>'
        '<div class="ch-list" style="margin-top:26px">' + "".join(rows) + '</div>'
    )
    return page_shell("章节解读", base, "chapters", inner,
                      "AI Native 组织章节深度解读目录")


# ------------------------------------------------------------- book 2 pages

def _b2_chapter_meta(deep_slug: str) -> dict:
    return next(c for c in BOOK2["chapters"] if c.get("deep") == deep_slug)


def render_b2_chapter_page(deep_slug: str, base: str) -> str:
    doc = BRAND2_CONTENT[deep_slug]
    c = _b2_chapter_meta(deep_slug)
    blocks = doc["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    idx = next(i for i, x in enumerate(BRAND2_DEEP) if x["deep"] == deep_slug)
    prev_c = BRAND2_DEEP[idx - 1] if idx > 0 else None
    next_c = BRAND2_DEEP[idx + 1] if idx + 1 < len(BRAND2_DEEP) else None
    pager = '<nav class="pager">'
    pager += (f'<a href="{base}brand2/{prev_c["deep"]}.html"><span class="dir-label">← 上一篇精读</span>'
              f'<span class="ttl">第 {prev_c["no"]} 章 · {escape(prev_c["title"])}</span></a>' if prev_c
              else '<span></span>')
    pager += (f'<a class="next" href="{base}brand2/{next_c["deep"]}.html"><span class="dir-label">下一篇精读 →</span>'
              f'<span class="ttl">第 {next_c["no"]} 章 · {escape(next_c["title"])}</span></a>' if next_c
              else '<span></span>')
    pager += '</nav>'
    chars = sum(len(str(v)) for b in blocks for v in b.values())
    minutes = max(8, round(chars / 900))
    inner = (
        f'<div class="crumb"><a href="{base}index.html">首页</a><span>/</span>'
        f'<a href="{base}brand2/index.html">品牌书·弱品牌强品牌</a><span>/</span>'
        f'<span>第 {c["no"]} 章</span></div>'
        f'<div class="cat">{escape(BOOK2["short_title"])} · 第 {c["no"]} 章 · 精读</div>'
        f'<h1>{escape(c["title"])}</h1>'
        f'<p class="lead">{inline(doc.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>原书页码 <b>{escape(c.get("pages", "—"))}</b></span>'
        f'<span>约 <b>{minutes}</b> 分钟读完</span>'
        f'<span>全书进度 <b>{c["no"]} / 25</b></span>'
        '<span>状态 <b>深度解读已发布</b></span></div></div>'
        + body_html + pager
    )
    title = f'第{c["no"]}章 {c["title"]}'
    return reader_page(base, deep_slug, inner, heads, title,
                       doc.get("lead", "")[:120], nav_current="brand2",
                       sidebar=sidebar_html_b2(base, deep_slug))


def _b2_row(c: dict, base: str) -> str:
    anchor = f' id="ch-{c["no"]}"'
    deep = c.get("deep")
    if deep and deep in BRAND2_CONTENT:
        return (f'<div class="ch-item live"{anchor}>'
                f'<span class="no">{c["no"]}</span>'
                f'<span class="t"><a href="{base}brand2/{deep}.html">{escape(c["title"])}</a>'
                f'<small>{escape(c.get("essence", ""))}</small></span>'
                f'<span class="st">精读已发布 · {c.get("pages", "—")}页</span></div>')
    return (f'<div class="ch-item"{anchor}>'
            f'<span class="no">{c["no"]}</span>'
            f'<span class="t">{escape(c["title"])}<small>{escape(c.get("essence", ""))}</small></span>'
            f'<span class="st"><span class="soon">框架索引</span></span></div>')


def render_b2_index(base: str) -> str:
    paths = "".join(
        f'<div class="path-card"><h4>{escape(p["name"])}</h4><p>{escape(p["desc"])}</p>'
        f'<div class="path-seq">{escape(p["seq"])}</div></div>'
        for p in BOOK2["reading_paths"])
    grouped = []
    for part in BOOK2["parts"]:
        part_rows = "".join(_b2_row(c, base) for c in BOOK2["chapters"]
                            if c["part"] == part["key"])
        grouped.append(
            f'<h3 style="margin:30px 0 4px">{escape(part["name"])}</h3>'
            f'<p style="font-size:13px;color:#8a97a8;margin:0 0 10px">{escape(part["desc"])} · 第 {escape(part["chapters"])} 章</p>'
            f'<div class="ch-list">{part_rows}</div>')
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span><span>品牌书·弱品牌强品牌</span></div>'
        '<div class="cat">BOOK TWO · BRAND GROWTH</div>'
        f'<h1>{escape(BOOK2["title"])}</h1>'
        f'<p class="lead">{escape(BOOK2.get("thesis", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>作者 <b>{escape(BOOK2["author"])}</b></span>'
        f'<span>出版社 <b>{escape(BOOK2["publisher"])}</b></span>'
        f'<span>ISBN <b>{escape(BOOK2["isbn"])}</b></span>'
        f'<span>出版 <b>{escape(BOOK2.get("pub_date", "2022.1"))}</b></span>'
        f'<span>正文 <b>{BOOK2.get("pages", "185")} 页</b></span>'
        f'<span>精读 <b>{len(BRAND2_DEEP)} / 25 章</b></span></div></div>'
        f'<div class="note" style="margin:18px 0">{escape(BOOK2.get("source_note", ""))}本站对该书采用「全书地图 + 战略章节精读」结构：25 章全部收录为框架索引，其中 {len(BRAND2_DEEP)} 个对跨境电商品牌域最关键的章节提供与第一本书同规格的深度解读（含实践映射）。</div>'
        + "".join(grouped)
        + '<h2 style="margin-top:44px">三条阅读路径</h2>'
        + f'<div class="path-grid" style="margin-top:14px">{paths}</div>'
        + '<div class="cta-card" style="margin-top:34px"><div><span class="idx">SYNTHESIS</span>'
        '<h3>两书合璧：AI Native 组织 × 品牌增长方法论</h3>'
        '<p>两本书的分工、五层结合点、智能中枢能力清单、FLOW-09 品效边界工程化与 Momcozy 诊断速览——整合方案的总入口。</p></div>'
        + f'<a class="go" href="{base}synthesis.html">打开合璧页 →</a></div>'
    )
    return page_shell(f'{BOOK2["short_title"]} · 全书地图', base, "brand2", inner,
                      BOOK2.get("thesis", "")[:120])


def _b3_chapter_meta(deep_slug: str) -> dict:
    for c in BOOK3["chapters"]:
        if c.get("deep") == deep_slug:
            return c
    return {}


def render_b3_chapter_page(deep_slug: str, base: str) -> str:
    doc = BOOK3_CONTENT[deep_slug]
    c = _b3_chapter_meta(deep_slug)
    blocks = doc["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    idx = next(i for i, x in enumerate(BOOK3_DEEP) if x["deep"] == deep_slug)
    prev_c = BOOK3_DEEP[idx - 1] if idx > 0 else None
    next_c = BOOK3_DEEP[idx + 1] if idx + 1 < len(BOOK3_DEEP) else None
    pager = '<nav class="pager">'
    pager += (f'<a href="{base}book3/{prev_c["deep"]}.html"><span class="dir-label">← 上一篇精读</span>'
              f'<span class="ttl">第 {prev_c["no"]} 章 · {escape(prev_c["title"])}</span></a>' if prev_c
              else '<span></span>')
    pager += (f'<a class="next" href="{base}book3/{next_c["deep"]}.html"><span class="dir-label">下一篇精读 →</span>'
              f'<span class="ttl">第 {next_c["no"]} 章 · {escape(next_c["title"])}</span></a>' if next_c
              else '<span></span>')
    pager += '</nav>'
    chars = sum(len(str(v)) for b in blocks for v in b.values())
    minutes = max(8, round(chars / 900))
    inner = (
        f'<div class="crumb"><a href="{base}index.html">首页</a><span>/</span>'
        f'<a href="{base}book3/index.html">本体书·本体驱动AI数据管理</a><span>/</span>'
        f'<span>第 {c["no"]} 章</span></div>'
        f'<div class="cat">{escape(BOOK3["short_title"])} · 第 {c["no"]} 章 · 精读</div>'
        f'<h1>{escape(c["title"])}</h1>'
        f'<p class="lead">{inline(doc.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>原书页码 <b>{escape(c.get("pages", "—"))}</b></span>'
        f'<span>约 <b>{minutes}</b> 分钟读完</span>'
        f'<span>全书进度 <b>{c["no"]} / 10</b></span>'
        '<span>状态 <b>深度解读已发布</b></span></div></div>'
        + body_html + pager
    )
    title = f'第{c["no"]}章 {c["title"]}'
    return reader_page(base, deep_slug, inner, heads, title,
                       doc.get("lead", "")[:120], nav_current="book3",
                       sidebar=sidebar_html_b3(base, deep_slug))


def _b3_row(c: dict, base: str) -> str:
    anchor = f' id="ch-{c["no"]}"'
    deep = c.get("deep")
    if deep and deep in BOOK3_CONTENT:
        return (f'<div class="ch-item live"{anchor}>'
                f'<span class="no">{c["no"]}</span>'
                f'<span class="t"><a href="{base}book3/{deep}.html">{escape(c["title"])}</a>'
                f'<small>{escape(c.get("essence", ""))}</small></span>'
                f'<span class="st">精读已发布 · {c.get("pages", "—")}页</span></div>')
    return (f'<div class="ch-item"{anchor}>'
            f'<span class="no">{c["no"]}</span>'
            f'<span class="t">{escape(c["title"])}<small>{escape(c.get("essence", ""))}</small></span>'
            f'<span class="st"><span class="soon">框架索引</span></span></div>')


def render_b3_index(base: str) -> str:
    paths = "".join(
        f'<div class="path-card"><h4>{escape(p["name"])}</h4><p>{escape(p["desc"])}</p>'
        f'<div class="path-seq">{escape(p["seq"])}</div></div>'
        for p in BOOK3["reading_paths"])
    grouped = []
    for part in BOOK3["parts"]:
        part_rows = "".join(_b3_row(c, base) for c in BOOK3["chapters"]
                            if c["part"] == part["key"])
        grouped.append(
            f'<h3 style="margin:30px 0 4px">{escape(part["name"])}</h3>'
            f'<p style="font-size:13px;color:#8a97a8;margin:0 0 10px">{escape(part["desc"])} · 第 {escape(part["chapters"])} 章</p>'
            f'<div class="ch-list">{part_rows}</div>')
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span><span>本体书·本体驱动AI数据管理</span></div>'
        '<div class="cat">BOOK THREE · SEMANTIC FOUNDATION</div>'
        f'<h1>{escape(BOOK3["title"])}</h1>'
        f'<p class="lead">{escape(BOOK3.get("thesis", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>作者 <b>{escape(BOOK3["author"])}</b></span>'
        f'<span>出版社 <b>{escape(BOOK3["publisher"])}</b></span>'
        f'<span>ISBN <b>{escape(BOOK3["isbn"])}</b></span>'
        f'<span>出版 <b>{escape(BOOK3.get("pub_date", "2026.5"))}</b></span>'
        f'<span>正文 <b>{BOOK3.get("pages", "211")} 页</b></span>'
        f'<span>精读 <b>{len(BOOK3_DEEP)} / 10 章</b></span></div></div>'
        f'<div class="note" style="margin:18px 0">{escape(BOOK3.get("source_note", ""))}本站对该书采用「全书地图 + 战略章节精读」结构：10 章全部收录为框架索引，其中 {len(BOOK3_DEEP)} 个与语义底座最相关的章节提供深度解读（含实践映射）。本书在本站的角色是语义底座层的方法源——其工程化成果已落成<a href="{base}semantic.html">语义底座 v0 全景页</a>。</div>'
        + "".join(grouped)
        + '<h2 style="margin-top:44px">三条阅读路径</h2>'
        + f'<div class="path-grid" style="margin-top:14px">{paths}</div>'
        + f'<div class="cta-card" style="margin-top:34px"><div><span class="idx">SEMANTIC</span>'
        '<h3>语义底座 v0：本书方法的落地层</h3>'
        '<p>48 条术语、20 对象 34 关系、38 条契约规则、24 条权限四元组——本书方法论在 Momcozy 品牌域的第一份工程化产出。</p></div>'
        + f'<a class="go" href="{base}semantic.html">打开语义底座 →</a></div>'
    )
    return page_shell(f'{BOOK3["short_title"]} · 全书地图', base, "book3", inner,
                      BOOK3.get("thesis", "")[:120])


def _b4_chapter_meta(deep_slug: str) -> dict:
    for c in BOOK4["chapters"]:
        if c.get("deep") == deep_slug:
            return c
    return {}


def render_b4_chapter_page(deep_slug: str, base: str) -> str:
    doc = BOOK4_CONTENT[deep_slug]
    c = _b4_chapter_meta(deep_slug)
    blocks = doc["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    idx = next(i for i, x in enumerate(BOOK4_DEEP) if x["deep"] == deep_slug)
    prev_c = BOOK4_DEEP[idx - 1] if idx > 0 else None
    next_c = BOOK4_DEEP[idx + 1] if idx + 1 < len(BOOK4_DEEP) else None
    pager = '<nav class="pager">'
    pager += (f'<a href="{base}book4/{prev_c["deep"]}.html"><span class="dir-label">← 上一篇精读</span>'
              f'<span class="ttl">第 {prev_c["no"]} 章 · {escape(prev_c["title"])}</span></a>' if prev_c
              else '<span></span>')
    pager += (f'<a class="next" href="{base}book4/{next_c["deep"]}.html"><span class="dir-label">下一篇精读 →</span>'
              f'<span class="ttl">第 {next_c["no"]} 章 · {escape(next_c["title"])}</span></a>' if next_c
              else '<span></span>')
    pager += '</nav>'
    chars = sum(len(str(v)) for b in blocks for v in b.values())
    minutes = max(8, round(chars / 900))
    inner = (
        f'<div class="crumb"><a href="{base}index.html">首页</a><span>/</span>'
        f'<a href="{base}book4/index.html">Agent书·深入理解AI Agent</a><span>/</span>'
        f'<span>第 {c["no"]} 章</span></div>'
        f'<div class="cat">{escape(BOOK4["short_title"])} · 第 {c["no"]} 章 · 精读</div>'
        f'<h1>{escape(c["title"])}</h1>'
        f'<p class="lead">{inline(doc.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>原书 <b>Apache-2.0 开源书</b></span>'
        f'<span>约 <b>{minutes}</b> 分钟读完</span>'
        f'<span>全书进度 <b>{c["no"]} / 10</b></span>'
        '<span>状态 <b>深度解读已发布</b></span></div></div>'
        + body_html + pager
    )
    title = f'第{c["no"]}章 {c["title"]}'
    return reader_page(base, deep_slug, inner, heads, title,
                       doc.get("lead", "")[:120], nav_current="book4",
                       sidebar=sidebar_html_b4(base, deep_slug))


def _b4_row(c: dict, base: str) -> str:
    anchor = f' id="ch-{c["no"]}"'
    deep = c.get("deep")
    if deep and deep in BOOK4_CONTENT:
        return (f'<div class="ch-item live"{anchor}>'
                f'<span class="no">{c["no"]}</span>'
                f'<span class="t"><a href="{base}book4/{deep}.html">{escape(c["title"])}</a>'
                f'<small>{escape(c.get("essence", ""))}</small></span>'
                f'<span class="st">精读已发布</span></div>')
    return (f'<div class="ch-item"{anchor}>'
            f'<span class="no">{c["no"]}</span>'
            f'<span class="t">{escape(c["title"])}<small>{escape(c.get("essence", ""))}</small></span>'
            f'<span class="st"><span class="soon">框架索引</span></span></div>')


def render_b4_index(base: str) -> str:
    paths = "".join(
        f'<div class="path-card"><h4>{escape(p["name"])}</h4><p>{escape(p["desc"])}</p>'
        f'<div class="path-seq">{escape(p["seq"])}</div></div>'
        for p in BOOK4["reading_paths"])
    grouped = []
    for part in BOOK4["parts"]:
        part_rows = "".join(_b4_row(c, base) for c in BOOK4["chapters"]
                            if c["part"] == part["key"])
        grouped.append(
            f'<h3 style="margin:30px 0 4px">{escape(part["name"])}</h3>'
            f'<p style="font-size:13px;color:#8a97a8;margin:0 0 10px">{escape(part["desc"])} · 第 {escape(part["chapters"])} 章</p>'
            f'<div class="ch-list">{part_rows}</div>')
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span><span>Agent书·深入理解AI Agent</span></div>'
        '<div class="cat">BOOK FOUR · AGENT ENGINEERING</div>'
        f'<h1>{escape(BOOK4["title"])}</h1>'
        f'<p class="lead">{escape(BOOK4.get("thesis", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>作者 <b>{escape(BOOK4["author"])}</b></span>'
        f'<span>协议 <b>{escape(BOOK4.get("license", "Apache-2.0"))}</b></span>'
        f'<span>仓库 <b><a href="{BOOK4["repo"]}" style="color:var(--r-blue)">bojieli/ai-agent-book ↗</a></b></span>'
        f'<span>在线版 <b><a href="{BOOK4["online"]}" style="color:var(--r-blue)">bojieli.github.io ↗</a></b></span>'
        f'<span>精读 <b>{len(BOOK4_DEEP)} / 10 章</b></span></div></div>'
        f'<div class="note" style="margin:18px 0">{escape(BOOK4.get("source_note", ""))}本站对该书采用「全书地图 + 全章精读」结构：10 章全部提供原创深度解读（含实践映射），每章保留核心论点与工程实验入口作为框架索引。本书在本站的角色是运行时层的方法源——其工程概念与 <a href="{base}agent-lab.html">Agent 实验场</a> 三方映射、<a href="{base}stack.html">四层架构</a> 0→1 路径互为表里。</div>'
        + "".join(grouped)
        + '<h2 style="margin-top:44px">三条阅读路径</h2>'
        + f'<div class="path-grid" style="margin-top:14px">{paths}</div>'
        + f'<div class="cta-card" style="margin-top:34px"><div><span class="idx">MAPPING</span>'
        '<h3>Agent 实验场：书 × 代码 × 项目契约</h3>'
        '<p>26 个 ToyAgent 场景 × 10 章书 × 项目契约 ID 的三方映射——看一个 Agent 从公式到约束到评估的完整工程链路。</p></div>'
        + f'<a class="go" href="{base}agent-lab.html">打开实验场 →</a></div>'
        + f'<div class="cta-card" style="margin-top:14px"><div><span class="idx">REPRO</span>'
        '<h3>配套实验：110 个编号实验 + 22 份 Skill</h3>'
        '<p>每章可运行实验与配套代码目录直达 GitHub 仓库——读完想动手验证，从这里进。</p></div>'
        + f'<a class="go" href="{base}experiments.html">打开实验地图 →</a></div>'
        + f'<div class="cta-card" style="margin-top:14px"><div><span class="idx">PLAYBOOK</span>'
        '<h3>Agent Playbook：从 0 到 1 的构建路线</h3>'
        '<p>《AI Agent 通识教程》30 章按构建依赖重排为 P0–P8 节点——书4 讲每个零件的原理，Playbook 讲按什么顺序把它们装成一个能跑的 Agent。</p></div>'
        + f'<a class="go" href="{base}agent-playbook/index.html">打开 Playbook →</a></div>'
    )
    return page_shell(f'{BOOK4["short_title"]} · 全书地图', base, "book4", inner,
                      BOOK4.get("thesis", "")[:120])


def render_agent_lab(base: str) -> str:
    blocks = AGENT_LAB["blocks"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span><span>Agent实验场</span></div>'
        '<div class="cat">AGENT LAB · THREE-WAY MAP</div>'
        f'<h1>{escape(AGENT_LAB["title"])}</h1>'
        f'<p class="lead">{inline(AGENT_LAB.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>性质 <b>本站原创整合 · 非原书内容</b></span>'
        f'<span>约 <b>{AGENT_LAB.get("minutes", "12")}</b> 分钟读完</span>'
        '<span>覆盖 <b>书4 × ToyAgent 26 场景 × 项目契约</b></span></div></div>'
        + body_html
        + f'<div class="cta-card" style="margin-top:14px"><div><span class="idx">DISTILL</span>'
        '<h3>ToyAgent 原理文章：27 篇方法论蒸馏</h3>'
        '<p>每个 step 配一篇机制讲解——本站逐篇蒸馏为「定位 / 机制 / 边界 / 代码链接」，读机制细节从这里进。</p></div>'
        + f'<a class="go" href="{base}toyagent-steps.html">打开原理文章蒸馏 →</a></div>'
        + f'<div class="cta-card" style="margin-top:14px"><div><span class="idx">PLAYBOOK</span>'
        '<h3>Agent Playbook：从 0 到 1 的构建路线</h3>'
        '<p>AI Agent 通识教程 30 章按构建依赖重排为 P0–P8 节点——先跑通最小循环，再上可靠性与治理，最后按需扩展。</p></div>'
        + f'<a class="go" href="{base}agent-playbook/index.html">打开 Playbook →</a></div>'
        + f'<div class="cta-card" style="margin-top:14px"><div><span class="idx">STACK</span>'
        '<h3>四层架构：0→1 设计总纲</h3>'
        '<p>组织 × 业务 × 语义 × 工程四层如何拼成「AI Native Agent 从 0 到 1」的完整路径。</p></div>'
        + f'<a class="go" href="{base}stack.html">打开四层架构 →</a></div>')
    return reader_page(base, "", inner, heads, AGENT_LAB["title"],
                       AGENT_LAB.get("lead", "")[:120], nav_current="agent-lab")


def render_stack(base: str) -> str:
    blocks = STACK["blocks"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span><span>四层架构</span></div>'
        '<div class="cat">STACK · FOUR LAYERS</div>'
        f'<h1>{escape(STACK["title"])}</h1>'
        f'<p class="lead">{inline(STACK.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>性质 <b>本站原创整合 · 非原书内容</b></span>'
        f'<span>约 <b>{STACK.get("minutes", "10")}</b> 分钟读完</span>'
        '<span>覆盖 <b>四书 70 章框架 + 实战轨</b></span></div></div>'
        + body_html
        + f'<div class="cta-card" style="margin-top:14px"><div><span class="idx">PLAYBOOK</span>'
        '<h3>Agent Playbook：0→1 构建路线的施工顺序</h3>'
        '<p>四层架构回答「造出来的 Agent 由哪几层组成」；Playbook 回答「按什么顺序把它造出来」——P0–P8 构建脊柱 + 模型边界矩阵。</p></div>'
        + f'<a class="go" href="{base}agent-playbook/index.html">打开 Playbook →</a></div>')
    return reader_page(base, "", inner, heads, STACK["title"],
                       STACK.get("lead", "")[:120], nav_current="stack")


def _pb_node_meta(slug: str) -> dict:
    for n in AGENT_PLAYBOOK.get("nodes", []):
        if n.get("slug") == slug:
            return n
    return {}


def render_pb_node_page(slug: str, base: str) -> str:
    doc = AGENT_PLAYBOOK_CONTENT[slug]
    n = _pb_node_meta(slug)
    blocks = doc["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    idx = next(i for i, x in enumerate(AGENT_PLAYBOOK_NODES) if x["slug"] == slug)
    prev_n = AGENT_PLAYBOOK_NODES[idx - 1] if idx > 0 else None
    next_n = AGENT_PLAYBOOK_NODES[idx + 1] if idx + 1 < len(AGENT_PLAYBOOK_NODES) else None
    pager = '<nav class="pager">'
    pager += (f'<a href="{base}agent-playbook/{prev_n["slug"]}.html"><span class="dir-label">← 上一节点</span>'
              f'<span class="ttl">{prev_n["no"]} · {escape(prev_n["title"])}</span></a>' if prev_n
              else f'<a href="{base}agent-playbook/index.html"><span class="dir-label">← 框架总纲</span>'
                   f'<span class="ttl">0→1 路线图与模型边界矩阵</span></a>')
    pager += (f'<a class="next" href="{base}agent-playbook/{next_n["slug"]}.html"><span class="dir-label">下一节点 →</span>'
              f'<span class="ttl">{next_n["no"]} · {escape(next_n["title"])}</span></a>' if next_n
              else '<span></span>')
    pager += '</nav>'
    chars = sum(len(str(v)) for b in blocks for v in b.values())
    minutes = max(8, round(chars / 900))
    src_chapters = "、".join(n.get("chapters", []))
    inner = (
        f'<div class="crumb"><a href="{base}index.html">首页</a><span>/</span>'
        f'<a href="{base}agent-playbook/index.html">Agent Playbook</a><span>/</span>'
        f'<span>{n.get("no", "")}</span></div>'
        f'<div class="cat">PLAYBOOK · {n.get("no", "")} · {escape(n.get("phase", ""))} · {escape(n.get("tier", ""))}</div>'
        f'<h1>{escape(n.get("title", doc.get("title", "")))}</h1>'
        f'<p class="lead">{inline(doc.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>层级 <b>{escape(n.get("phase", ""))} · {escape(n.get("tier", ""))}</b></span>'
        f'<span>源章节 <b>{escape(src_chapters)}</b></span>'
        f'<span>约 <b>{minutes}</b> 分钟读完</span>'
        '<span>性质 <b>原创蒸馏 · 非教程转载</b></span></div></div>'
        + body_html + pager
    )
    title = f'{n.get("no", "")} {n.get("title", "")}'
    return reader_page(base, slug, inner, heads, title,
                       doc.get("lead", "")[:120], nav_current="agent-playbook",
                       sidebar=sidebar_html_pb(base, slug))


def render_agent_playbook(base: str) -> str:
    pb = AGENT_PLAYBOOK
    blocks = pb["blocks"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    n_pub = len(AGENT_PLAYBOOK_NODES)
    n_total = len(pb.get("nodes", []))
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span><span>Agent Playbook</span></div>'
        '<div class="cat">AGENT PLAYBOOK · 0 → 1 BUILD ROUTE</div>'
        f'<h1>{escape(pb["title"])}</h1>'
        f'<p class="lead">{inline(pb.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>来源 <b><a href="{pb.get("source_url", "https://ai-agent-guide.xiaofuge.cn/")}" style="color:var(--r-blue)">AI Agent 通识教程 30 章 ↗</a></b></span>'
        f'<span>节点 <b>{n_pub} / {n_total} 已发布</b></span>'
        '<span>基线 <b>DeepSeek Chat + Function Calling</b></span>'
        '<span>性质 <b>原创蒸馏 · 非教程转载</b></span></div></div>'
        + body_html
        + f'<div class="cta-card" style="margin-top:14px"><div><span class="idx">CONTEXT</span>'
        '<h3>Agent 实验场：书 × 代码 × 项目契约</h3>'
        '<p>26 个 ToyAgent 场景 × 书4 章节 × 项目契约 ID 的三方映射——看每个工程概念落到代码与契约的样子。</p></div>'
        + f'<a class="go" href="{base}agent-lab.html">打开实验场 →</a></div>'
        + f'<div class="cta-card" style="margin-top:14px"><div><span class="idx">DEPTH</span>'
        '<h3>Agent书 · 深入理解 AI Agent：10 章全章精读</h3>'
        '<p>同一主题的原理纵深版——本 playbook 讲「按什么顺序造」，书4 精读讲「每个零件为什么这样设计」。</p></div>'
        + f'<a class="go" href="{base}book4/index.html">打开 Agent书 →</a></div>'
        + f'<div class="cta-card" style="margin-top:14px"><div><span class="idx">STEPS</span>'
        '<h3>ToyAgent 原理文章：27 篇机制蒸馏</h3>'
        '<p>26 个可运行场景各配一篇机制讲解——本 playbook 的每个节点都能在那里找到对应的可运行参照。</p></div>'
        + f'<a class="go" href="{base}toyagent-steps.html">打开原理文章 →</a></div>')
    return reader_page(base, "", inner, heads, pb["title"],
                       pb.get("lead", "")[:120], nav_current="agent-playbook",
                       sidebar=sidebar_html_pb(base, ""))


def render_experiments(base: str) -> str:
    """Book4 companion experiments + skills index page."""
    repo = EXPERIMENTS["repo"]
    ch_title = {int(c["no"]): c["title"] for c in BOOK4["chapters"]}
    deep_of = {int(c["no"]): c.get("deep", "") for c in BOOK4["chapters"]}
    n_exp = sum(len(c["experiments"]) for c in EXPERIMENTS["chapters"])
    n_dir = sum(len(c["dirs"]) for c in EXPERIMENTS["chapters"])

    parts = [
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span>'
        '<a href="' + base + 'book4/index.html">Agent书</a><span>/</span><span>配套实验</span></div>',
        '<div class="cat">BOOK4 · EXPERIMENTS &amp; SKILLS</div>',
        f'<h1>配套实验与主题 Skill（{n_exp} 实验 · {n_dir} 代码目录 · {len(EXPERIMENTS["skills"])} Skill）</h1>',
        '<p class="lead">《深入理解 AI Agent》每章配有可运行实验与配套代码——Apache-2.0 开源在 '
        f'<a href="{repo}" target="_blank" rel="noopener">bojieli/ai-agent-book</a> 仓库的 '
        '<code>chapter1~10/</code> 目录；另有 22 份主题 SKILL.md 把各章方法封装为可复用 Agent Skill。'
        '下表按章列出书中编号实验（★ 为书中推荐度）、验证目标与对应代码目录；实验编号与精读页内容一一对应。</p>',
        '<div class="note" style="margin:18px 0">使用方式：多数实验需要 API Key 或本地模型，README 内含环境准备、运行命令与预期现象。'
        '标注「代码」的实验可点击直达对应目录；未标注的实验为论文复现或需要硬件（机器人/语音设备）的进阶项目，代码入口见章末目录清单。</div>',
    ]

    for c in EXPERIMENTS["chapters"]:
        no = c["no"]
        title = ch_title.get(no, f"第{no}章")
        deep = deep_of.get(no, "")
        head_link = (f'<a href="{base}book4/{deep}.html" style="color:var(--r-blue)">{escape(title)}</a>'
                     if deep else escape(title))
        rows = []
        for e in c["experiments"]:
            code_cell = ""
            if e["code"]:
                code_cell = (f'<a href="{repo}/tree/main/chapter{no}/{e["code"]}" target="_blank" rel="noopener">'
                             f'<code>{escape(e["code"])}</code> ↗</a>')
            else:
                code_cell = (f'<a href="{repo}/tree/main/chapter{no}" target="_blank" rel="noopener">章目录 ↗</a>')
            stars = e["stars"] or "—"
            rows.append(
                f'<tr><td class="mono">{e["id"]}</td><td>{stars}</td>'
                f'<td><b>{escape(e["title"])}</b><br><span style="color:#8a97a8;font-size:13px">{escape(e["desc"])}</span></td>'
                f'<td style="white-space:nowrap">{code_cell}</td></tr>')
        # extra dirs not mapped to a numbered experiment
        extra = [d for d in c["dirs"] if not d["exp"]]
        extra_html = ""
        if extra:
            links = "".join(
                f'<a href="{repo}/tree/main/chapter{no}/{d["name"]}" target="_blank" rel="noopener" '
                f'style="display:inline-block;margin:2px 8px 2px 0;padding:2px 10px;border:1px solid #d8dee8;'
                f'border-radius:999px;font-size:12.5px;color:var(--r-blue);text-decoration:none">'
                f'{escape(d["name"])} ↗</a>' for d in extra)
            extra_html = ('<p style="margin:10px 0 4px;font-size:13px;color:#8a97a8">附加代码目录（书中未单独编号）：</p>'
                          f'<div>{links}</div>')
        parts.append(
            f'<h2 id="ch-{no}"><span class="sec-no">{no:02d}</span>{head_link}</h2>'
            '<div class="table-wrap"><table><thead><tr><th style="width:64px">编号</th><th style="width:56px">推荐</th>'
            '<th>实验与验证目标</th><th style="width:170px">代码</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div>' + extra_html)

    # skills section
    sk_rows = []
    for s in EXPERIMENTS["skills"]:
        sk_rows.append(
            f'<tr><td class="mono"><a href="{EXPERIMENTS["skill_repo"]}/{s["dir"]}" target="_blank" rel="noopener">'
            f'{escape(s["dir"])} ↗</a></td><td><b>{escape(s["name"])}</b><br>'
            f'<span style="color:#8a97a8;font-size:13px">{escape(s["desc"])}</span></td></tr>')
    parts.append(
        '<h2 id="skills"><span class="sec-no">SK</span>主题 Skill 索引（22 份）</h2>'
        '<p style="color:#8a97a8;font-size:14px;margin:-6px 0 14px">书中配套的 Agent Skill——把各章方法封装为标准 SKILL.md，'
        '可直接放入 Agent 运行环境按需加载；与本站<a href="' + base + 'agent-lab.html" style="color:var(--r-blue)">三方映射</a>'
        '中「Skill 按需加载」的工程实践互为印证。</p>'
        '<div class="table-wrap"><table><thead><tr><th style="width:220px">Skill 目录</th><th>用途</th></tr></thead><tbody>'
        + "".join(sk_rows) + '</tbody></table></div>')

    inner = "".join(parts)
    inner += (f'<div class="cta-card" style="margin-top:30px"><div><span class="idx">NEXT</span>'
              '<h3>回到 Agent书全书地图</h3>'
              '<p>10 章全章精读、三条阅读路径与官方在线版入口。</p></div>'
              + f'<a class="go" href="{base}book4/index.html">Agent书全书地图 →</a></div>')
    return page_shell("配套实验与主题 Skill · Agent书", base, "experiments", inner,
                      "《深入理解 AI Agent》配套实验地图：110 个编号实验、111 个代码目录与 22 份主题 SKILL.md，按章索引并直达 GitHub 仓库。")


def render_toyagent_steps(base: str) -> str:
    blocks = TOYAGENT_STEPS["blocks"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span>'
        '<a href="' + base + 'agent-lab.html">Agent实验场</a><span>/</span><span>ToyAgent 原理文章</span></div>'
        '<div class="cat">AGENT LAB · ARTICLE DISTILLATION</div>'
        f'<h1>{escape(TOYAGENT_STEPS["title"])}</h1>'
        f'<p class="lead">{inline(TOYAGENT_STEPS.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>性质 <b>本站原创蒸馏 · 非原文转载</b></span>'
        f'<span>约 <b>{escape(TOYAGENT_STEPS.get("minutes", "18"))}</b> 分钟读完</span>'
        '<span>覆盖 <b>27 篇原理文章 × 26 场景 × 7 弧线</b></span></div></div>'
        + body_html
        + f'<div class="cta-card" style="margin-top:30px"><div><span class="idx">MAP</span>'
        '<h3>Agent 实验场：三方映射总表</h3>'
        '<p>每个 step 与书4 章节、项目契约 ID 的映射——先建坐标再读机制。</p></div>'
        + f'<a class="go" href="{base}agent-lab.html">打开三方映射 →</a></div>')
    return reader_page(base, "", inner, heads, TOYAGENT_STEPS["title"],
                       TOYAGENT_STEPS.get("lead", "")[:120], nav_current="toyagent-steps")


def render_trilogy(base: str) -> str:
    blocks = TRILOGY["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span><span>三书合璧</span></div>'
        '<div class="cat">TRILOGY · THREE BOOKS</div>'
        f'<h1>{escape(TRILOGY["title"])}</h1>'
        f'<p class="lead">{inline(TRILOGY.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>性质 <b>本站原创整合 · 非原书内容</b></span>'
        f'<span>约 <b>{TRILOGY.get("minutes", "12")}</b> 分钟读完</span>'
        '<span>覆盖 <b>三书 60 章框架</b></span></div></div>'
        + body_html
        + f'<div class="cta-card" style="margin-top:30px"><div><span class="idx">DETAIL</span>'
        '<h3>两书合璧：书1 × 书2 深度整合</h3>'
        '<p>AI Native 组织 × 品牌增长方法论的分工、五层结合点、智能中枢能力清单与 FLOW-09 品效边界工程化——两书间的细粒度整合见专页。</p></div>'
        + f'<a class="go" href="{base}synthesis.html">打开两书合璧 →</a></div>')
    return reader_page(base, "", inner, heads, TRILOGY["title"],
                       TRILOGY.get("lead", "")[:120], nav_current="triology")


def render_synthesis(base: str) -> str:
    blocks = SYNTHESIS["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span><span>两书合璧</span></div>'
        '<div class="cat">SYNTHESIS · BRIDGE</div>'
        f'<h1>{escape(SYNTHESIS["title"])}</h1>'
        f'<p class="lead">{inline(SYNTHESIS.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>性质 <b>本站原创整合 · 非原书内容</b></span>'
        f'<span>约 <b>{SYNTHESIS.get("minutes", "15")}</b> 分钟读完</span>'
        '<span>覆盖 <b>两书 40 章框架</b></span></div></div>'
        + body_html)
    return reader_page(base, "", inner, heads, SYNTHESIS["title"],
                       SYNTHESIS.get("lead", "")[:120], nav_current="synthesis")


def render_home(base: str) -> str:
    parts = [
        ("上篇", "道", "理解 AI Native 组织的底层逻辑：知识如何路由、主体如何切换、增长在哪里裂缝。", "ch01-xinxi-luyou,ch02-zhuanti-qiehuan,ch03-xiaolv-yuzengzhang"),
        ("中篇", "术", "建立人机协作的方法：知识编码、目标与边界、持续进化、角色与架构。", "ch04-zhishi-bianma,ch05-mubiao-yu-bianjie,ch06-zhixu-jinhua,ch07-jiaose-yu-jiagou"),
        ("下篇", "器", "企业级落地：Agent 平台、信任工程、文化、转型路线图、行业心跳与个人选择。", "ch08-agent-pingtai,ch09-xinren-gongcheng,ch10-wenhua,ch11-zhuanxing-luxian,ch12-hangye-xinbo,ch13-geren-xuanze"),
    ]
    cards = []
    for pn, pk, desc, chs in parts:
        ch_links = ""
        for slug in chs.split(","):
            c = next(x for x in CHAPTERS if x["slug"] == slug)
            if c["slug"] in CHAPTER_CONTENT:
                ch_links += f'<a href="{base}chapters/{c["slug"]}.html">{c["no"]} {escape(c["title"])}</a><br>'
            else:
                ch_links += f'{c["no"]} {escape(c["title"])}<br>'
        cards.append(
            f'<div class="map-card"><span class="part">{pn}篇 · {pk}</span><h3>{escape(pn)}篇</h3>'
            f'<p>{escape(desc)}</p><div class="chs">{ch_links}</div></div>')
    live_chapters = [c for c in CHAPTERS if c["slug"] in CHAPTER_CONTENT]
    pending = [c for c in CHAPTERS if c["slug"] not in CHAPTER_CONTENT]
    ch_rows = "".join(
        f'<div class="ch-item live"><span class="no">{c["no"]}</span>'
        f'<span class="t"><a href="{base}chapters/{c["slug"]}.html">{escape(c["title"])}</a>'
        f'<small>第 {c["no"]} 章 · {escape(c.get("part_name", ""))} · 原书 {c.get("pages", "—")} 页</small></span>'
        f'<span class="st">已发布</span></div>'
        for c in live_chapters)
    ch_rows += "".join(
        f'<div class="ch-item"><span class="no">{c["no"]}</span>'
        f'<span class="t">{escape(c["title"])}<small>{escape(c.get("part_name", ""))}</small></span>'
        f'<span class="st"><span class="soon">撰写中</span></span></div>'
        for c in pending)
    concept_cards = "".join(
        f'<div class="concept-card"><h3><a href="{base}concepts/index.html#{c["slug"]}">{escape(c["term"])}</a></h3>'
        f'<p>{escape(c["definition"])}</p>'
        f'<div class="from">出自 {"、".join(_from_html(x, base) for x in c.get("from", []))}</div></div>'
        for c in CONCEPTS[:8])
    tool_cards = "".join(
        f'<div class="tool-card"><span class="idx">TOOL {t["idx"]:02d}</span><h3>{escape(t["name"])}</h3>'
        f'<p>{escape(t["desc"])}</p><a class="go" href="{base}tools/{t["slug"]}.html">打开工具 →</a></div>'
        for t in TOOLS)
    n_assets = sum(len(g["items"]) for g in PILOT_ASSETS["groups"])
    hero = f"""
<section class="hero"><div class="wrap">
<div>
<p class="eyebrow">READING NOTES × AI NATIVE PRACTICE</p>
<h1>Native AI Organ</h1>
<p class="lead">《AI Native 组织：从思考到实践》《弱品牌强品牌》《本体驱动的AI数据管理》《深入理解 AI Agent》四本书的原创深度解读——以及 AI Native 组织变革方案的实战化公开版。读书笔记与实战项目，同一仓库。</p>
<div class="meta">
<div><b>4</b>本书</div>
<div><b>{len(CHAPTERS) + len(BOOK2["chapters"]) + len(BOOK3["chapters"]) + len(BOOK4["chapters"])}</b>章框架</div>
<div><b>{len(CHAPTER_CONTENT) + len(BRAND2_DEEP) + len(BOOK3_DEEP) + len(BOOK4_DEEP)}</b>篇精读</div>
<div><b>20</b>场景规格</div>
<div><b>{n_assets}</b>项资产</div>
</div></div>
<div class="book-card"><div class="kicker">THE SITE</div>
<h2>站点构成</h2>
<div class="site-entries">
<div class="site-entry"><b>书一 · AI Native 组织</b><span>《{escape(BOOK['title'])}》{escape(BOOK['author'])} 著 · {len(CHAPTER_CONTENT)} 篇深度解读</span><a href="{base}chapters/index.html">章节解读 →</a></div>
<div class="site-entry"><b>书二 · 弱品牌强品牌</b><span>《{escape(BOOK2["short_title"])}》{escape(BOOK2["author"])} 著 · {len(BOOK2["chapters"])} 章框架 + {len(BRAND2_DEEP)} 篇精读</span><a href="{base}brand2/index.html">品牌书全书地图 →</a></div>
<div class="site-entry"><b>书三 · 本体驱动的AI数据管理</b><span>《{escape(BOOK3["short_title"])}》{escape(BOOK3["author"])} 著 · {len(BOOK3["chapters"])} 章框架 + {len(BOOK3_DEEP)} 篇精读</span><a href="{base}book3/index.html">本体书全书地图 →</a></div>
<div class="site-entry"><b>书四 · 深入理解 AI Agent</b><span>《{escape(BOOK4["short_title"])}》{escape(BOOK4["author"])} 著 · Apache-2.0 开源书 · {len(BOOK4["chapters"])} 章框架 + {len(BOOK4_DEEP)} 篇精读</span><a href="{base}book4/index.html">Agent书全书地图 →</a></div>
<div class="site-entry"><b>Agent Playbook · 0→1</b><span>AI Agent 通识教程 30 章蒸馏：P0–P8 构建脊柱 + 模型边界矩阵（DeepSeek 基线）</span><a href="{base}agent-playbook/index.html">打开 Playbook →</a></div>
<div class="site-entry"><b>实战项目 · AI 组织变革</b><span>约 50 个 AI 岗位的组织变革方案公开版：20 场景规格、4 份 Skill 契约、语义底座方法、试点五件套、P0~P4 路线</span><a href="{base}brand-plan.html">实战路线图 →</a></div>
</div>
<a class="hero-sitemap" href="{base}sitemap.html">站点地图 · 不知从哪开始？→</a></div></div></section>"""
    chain = [
        ("序章", "凌晨三点的 Agent", "一个故障故事，提出全书的问题：当 Agent 开始独立做事，组织靠什么协调？", "prologue"),
        ("道 · 第 1–3 章", "为什么必须变", "组织是信息路由系统；做事主体从人切换到 AI；效率提升的裂缝在增长闭环中间两环", "ch01-xinxi-luyou"),
        ("术 · 第 4–7 章", "怎么分工与进化", "知识编码成 AI 读得懂的样子；目标与边界的人机分工；知识库到飞轮；角色取代岗位", "ch04-zhishi-bianma"),
        ("器 · 第 8–10 章", "平台与信任", "Agent 平台的感知行与七组件；信任的工程与治理十二道门；文化是不需要分发的上下文", "ch08-agent-pingtai"),
        ("第 11 章", "转型路线图", "先诊断、再重构流程、然后部署 Agent、最后走向网络——波定方向，闭环定节拍", "ch11-zhuanxing-luxian"),
        ("第 12 章", "行业的心跳", "同一套方法在游戏、零售、金融、制造、B2B 软件五个行业的变体", "ch12-hangye-xinbo"),
        ("第 13 章 · 终章", "个人与 CEO", "AI 时代的个人资产负债表；写给一号位的信", "ch13-geren-xuanze"),
    ]
    chain_html = '<div class="chain">' + "".join(
        f'<a class="chain-node" href="{base}chapters/{slug}.html"><b>{escape(t)}</b>'
        f'<span>{escape(q)}</span><em>{escape(d)}</em></a>' for t, q, d, slug in chain) + '</div>'
    paths = [
        ("布道者路径", "先建立认知与路线共识，再谈工程", "序章 → 第 1、2、3 章 → 第 11 章 → 终章"),
        ("实操者路径", "先拿边界与平台，再补全方法", "第 5 章 → 第 4、6、9 章 → 第 8 章 → 第 11 章"),
        ("个人路径", "先看清自己的位置，再决定学什么", "第 13 章 → 第 5、6 章 → 终章"),
    ]
    path_html = '<div class="path-grid">' + "".join(
        f'<div class="path-card"><h4>{escape(n)}</h4><p>{escape(d)}</p>'
        f'<div class="path-seq">{escape(seq)}</div></div>' for n, d, seq in paths) + '</div>'
    b2_deep_rows = "".join(
        f'<div class="ch-item live"><span class="no">{c["no"]}</span>'
        f'<span class="t"><a href="{base}brand2/{c["deep"]}.html">{escape(c["title"])}</a>'
        f'<small>{escape(c.get("essence", ""))}</small></span>'
        f'<span class="st">精读</span></div>'
        for c in BRAND2_DEEP)
    b3_deep_rows = "".join(
        f'<div class="ch-item live"><span class="no">{c["no"]}</span>'
        f'<span class="t"><a href="{base}book3/{c["deep"]}.html">{escape(c["title"])}</a>'
        f'<small>{escape(c.get("essence", ""))}</small></span>'
        f'<span class="st">精读</span></div>'
        for c in BOOK3_DEEP)
    b4_deep_rows = "".join(
        f'<div class="ch-item live"><span class="no">{c["no"]}</span>'
        f'<span class="t"><a href="{base}book4/{c["deep"]}.html">{escape(c["title"])}</a>'
        f'<small>{escape(c.get("essence", ""))}</small></span>'
        f'<span class="st">精读</span></div>'
        for c in BOOK4_DEEP)
    track_cards = [
        ("读书笔记轨 · READING",
         "四本书的原创深度解读——先理解方法论本身：AI Native 组织怎么变、品牌增长该干什么、机器如何懂业务、一个 Agent 怎么被造出来，干得好是什么样。",
         [("章节解读", "书1 · 15 篇深度解读", "chapters/index.html"),
          ("品牌书·弱品牌强品牌", "书2 · 25 章框架 + 8 篇精读", "brand2/index.html"),
          ("本体书·本体驱动AI数据管理", "书3 · 10 章框架 + 6 篇精读", "book3/index.html"),
          ("Agent书·深入理解AI Agent", "书4 · 10 章全章精读（Apache-2.0 开源书）", "book4/index.html"),
          ("Agent Playbook·0到1", "教程30章→P0-P8构建脊柱+模型边界", "agent-playbook/index.html"),
          ("Agent实验场", "书4 × ToyAgent × 项目契约三方映射", "agent-lab.html"),
          ("四层架构", "组织×业务×语义×工程 0→1 路径", "stack.html"),
          ("三书合璧", "组织 × 品牌 × 语义三层支撑", "triology.html"),
          ("两书合璧", "书1×书2 分工与五层结合点", "synthesis.html"),
          ("概念索引", "44 个核心概念词条", "concepts/index.html"),
          ("随书工具", "6 件可勾选实操清单", "tools/index.html")]),
        ("实战项目轨 · PRACTICE",
         "AI 组织变革方案的实战化公开版——看同一套方法论如何落成约 50 个 AI 岗位的组织设计，并在 Momcozy 品牌域走到试点门前。全部为设计基线，不构成业务授权。",
         [("从书到试点", "读完书第一步做什么", "pilot.html"),
          ("试点资产地图", "45 项设计资产可点查规格", "pilot-assets.html"),
          ("实战路线图", "P0~P4 阶段门与场景波次", "brand-plan.html"),
          ("组织与价值流一张图", "50 岗位 × 13 流 × 20 场景交互图", "orgmap.html"),
          ("Sage 产品层规划", "出海产品 v5：52 场景 117 工作", "product.html"),
          ("方案术语表", "内部代号 D-020~D-053 解码", "terms.html"),
          ("3D 组织空间", "外部门户 · 交互原型", "https://native.sagegogo.com/src/orgmap/")]),
    ]
    def _track_links(links):
        return "".join(
            f'<a href="{href if "://" in href else base + href}">{escape(n)}<small>{escape(s)}</small></a>'
            for n, s, href in links)
    track_html = "".join(
        f'<div class="path-card track-card"><h4>{escape(t)}</h4><p>{escape(d)}</p>'
        f'<div class="track-links">{_track_links(links)}</div></div>'
        for t, d, links in track_cards)
    practice_items = [
        ("BRIDGE", "从书到试点", "读完书第一步做什么——价值链断点地图、首个 Case 模板、授权八问实例、十二道门、90 天节奏与 KPI 口径，全部写成可对照的操作清单。本站原创，非原书内容，不构成任何业务授权。", "pilot.html", "打开试点指南 →"),
        ("ASSETS", "试点资产地图", "45 项设计资产：FLOW-09 价值流、20 份场景规格、4 份 Skill 契约、语义底座十件套（含术语表、两份契约与对象模型/权限声明）、双层 KPI 字典、G1 企业交付包与试点五件套，每项可点查姊妹仓库规格原文。", "pilot-assets.html", "打开资产地图 →"),
        ("ROADMAP", "实战路线图", "品牌域从设计基线到 AI Native 实战案例的完整演进：六层结构（含语义底座层）、P0~P4 阶段门、20 场景波次、双层 KPI 落地与四本书理论锚点。", "brand-plan.html", "打开路线图 →"),
        ("ORGMAP", "组织与价值流一张图", "50 个 AI 岗位 × 13 条价值流 × 20 个业务场景的交互式绑定图：点选任意节点高亮全部绑定关系，四平面职责与跨平面契约一图看清。设计基线静态版。", "orgmap.html", "打开组织图 →"),
        ("SEMANTIC", "语义底座 v0", "《本体驱动的AI数据管理》吸收的落地层：48 条术语、20 对象 34 关系、38 条契约规则、24 条权限四元组——让机器真正懂 Momcozy 业务语义。全部 v0 基线，待数据激活。", "semantic.html", "打开语义底座 →"),
        ("PRODUCT", "Sage 产品层规划", "出海产品的完整蓝图：一个主产品 Sage（数字员工团队）+ 三个单点工具 + 四档购买，覆盖 Shopify/Amazon/TikTok Shop，52 个细分场景、117 项可验收工作，含两个标杆场景与七条主线。规划 v5，全为设计状态。", "product.html", "打开产品规划 →"),
    ]
    practice_html = "".join(
        f'<div class="cta-card"><div><span class="idx">{idx}</span><h3>{escape(t)}</h3>'
        f'<p>{escape(d)}</p></div><a class="go" href="{base}{href}">{escape(go)}</a></div>'
        for idx, t, d, href, go in practice_items)
    body = hero + f"""
<section class="section"><div class="wrap">
<h2>两条线：读书笔记 × 实战项目</h2>
<p class="sec-sub">本站由两条主线构成——笔记轨帮你理解方法论，实战轨让你看到方法论在一个真实业务域里长什么样。各板块的完整说明见<a href="{base}sitemap.html" style="color:var(--r-blue)">站点地图</a>。</p>
<div class="track-grid">{track_html}</div>
<p style="margin-top:16px;font-size:13px;color:#8a97a8">第一次来？建议按 <a href="{base}sitemap.html" style="color:var(--r-blue);font-weight:600">路径① 全站 30 分钟</a> 建立全貌。</p></div></section>
<section class="section tint"><div class="wrap">
<h2>全书地图</h2>
<p class="sec-sub">以「道—术—器」为主线：先理解原理，再建立方法，最后落地工程。每篇解读保留原书论证线，并附实践映射。</p>
<div class="map-grid">{''.join(cards)}</div></div></section>
<section class="section"><div class="wrap">
<h2>方法链：这本书为什么要按这个顺序读</h2>
<p class="sec-sub">每一层都以相邻层为前提：道回答「为什么」，术回答「怎么分工」，器回答「靠什么运行」，路线图回答「先做什么」，行业与个人回答「落到谁身上」。跳层阅读会得到结论，顺序阅读才能得到方法。</p>
{chain_html}
<h3 style="margin:34px 0 6px">三条推荐阅读路径</h3>
{path_html}</div></section>
<section class="section tint"><div class="wrap">
<h2>第二本书：《{escape(BOOK2["short_title"])}》</h2>
<p class="sec-sub">品牌域的业务方法论——与第一本书正交互补：书一回答 Agent 组织怎么建，书二回答品牌增长该干什么、干得好是什么样。本站采用「全书地图 + 战略章节精读」结构。</p>
<div class="cta-card">
<div><span class="idx">BOOK TWO</span><h3>{escape(BOOK2["title"])}</h3>
<p>{escape(BOOK2["author"])} 著 · {escape(BOOK2["publisher"])} · {escape(BOOK2["isbn"])} · 正文 {BOOK2.get("pages", "185")} 页 · {escape(BOOK2.get("thesis", ""))}</p></div>
<div style="display:flex;gap:10px;flex-wrap:wrap">
<a class="go" href="{base}brand2/index.html">品牌书全书地图 →</a>
<a class="go" href="{base}synthesis.html" style="background:transparent;border:1px solid var(--r-blue);color:var(--r-blue)">两书合璧 →</a></div></div>
<h3 style="margin:26px 0 6px">精选精读（{len(BRAND2_DEEP)} / 25 章）</h3>
<div class="ch-list">{b2_deep_rows}</div>
<p style="margin-top:14px;font-size:13px;color:#8a97a8">其余 {25 - len(BRAND2_DEEP)} 章收录为框架索引（含每章核心论点），见<a href="{base}brand2/index.html" style="color:var(--r-blue)">品牌书全书地图</a>。</p></div></section>
<section class="section"><div class="wrap">
<h2>第三本书：《{escape(BOOK3["short_title"])}》</h2>
<p class="sec-sub">语义底座层的方法论源头——与前两本书构成三层支撑：书一回答 AI 组织怎么变，书二回答品牌域该经营什么，书三回答机器如何懂业务。本站采用「全书地图 + 战略章节精读」结构。</p>
<div class="cta-card">
<div><span class="idx">BOOK THREE</span><h3>{escape(BOOK3["title"])}</h3>
<p>{escape(BOOK3["author"])} 著 · {escape(BOOK3["publisher"])} · {escape(BOOK3["isbn"])} · 正文 {BOOK3.get("pages", "211")} 页 · {escape(BOOK3.get("thesis", ""))}</p></div>
<div style="display:flex;gap:10px;flex-wrap:wrap">
<a class="go" href="{base}book3/index.html">本体书全书地图 →</a>
<a class="go" href="{base}semantic.html" style="background:transparent;border:1px solid var(--r-blue);color:var(--r-blue)">语义底座 v0 →</a></div></div>
<h3 style="margin:26px 0 6px">精选精读（{len(BOOK3_DEEP)} / 10 章）</h3>
<div class="ch-list">{b3_deep_rows}</div>
<p style="margin-top:14px;font-size:13px;color:#8a97a8">其余 {10 - len(BOOK3_DEEP)} 章收录为框架索引（含每章核心论点），见<a href="{base}book3/index.html" style="color:var(--r-blue)">本体书全书地图</a>；本书方法论的工程化落地见<a href="{base}semantic.html" style="color:var(--r-blue)">语义底座 v0 全景页</a>。</p></div></section>
<section class="section tint"><div class="wrap">
<h2>第四本书：《{escape(BOOK4["short_title"])}》</h2>
<p class="sec-sub">运行时层的方法源——前三本书回答组织怎么变、业务干什么、机器怎么懂，书四回答一个 Agent 怎么被造出来、跑起来、被约束。Apache-2.0 开源书，配套 ToyAgent 代码库做可运行参照。本站采用「全书地图 + 全章精读」结构。</p>
<div class="cta-card">
<div><span class="idx">BOOK FOUR</span><h3>{escape(BOOK4["title"])}</h3>
<p>{escape(BOOK4["author"])} 著 · {escape(BOOK4["publisher"])} · <a href="{BOOK4["repo"]}" style="color:inherit">GitHub ↗</a> · <a href="{BOOK4["online"]}" style="color:inherit">在线版 ↗</a> · {escape(BOOK4.get("thesis", ""))}</p></div>
<div style="display:flex;gap:10px;flex-wrap:wrap">
<a class="go" href="{base}book4/index.html">Agent书全书地图 →</a>
<a class="go" href="{base}agent-lab.html" style="background:transparent;border:1px solid var(--r-blue);color:var(--r-blue)">Agent实验场 →</a>
<a class="go" href="{base}stack.html" style="background:transparent;border:1px solid var(--r-blue);color:var(--r-blue)">四层架构 →</a></div></div>
<h3 style="margin:26px 0 6px">全章精读（{len(BOOK4_DEEP)} / 10 章）</h3>
<div class="ch-list">{b4_deep_rows}</div>
<p style="margin-top:14px;font-size:13px;color:#8a97a8">每章均含「实践映射」块——对照项目契约 ID；全书框架与官方原文入口见<a href="{base}book4/index.html" style="color:var(--r-blue)">Agent书全书地图</a>；书 × 代码 × 项目契约的三方映射见<a href="{base}agent-lab.html" style="color:var(--r-blue)">Agent 实验场</a>。</p></div></section>
<section class="section tint"><div class="wrap">
<h2>章节解读</h2>
<p class="sec-sub">已发布章节可直接阅读；其余章节正在蒸馏中。</p>
<div class="ch-list">{ch_rows}</div></div></section>
<section class="section tint"><div class="wrap">
<h2>概念索引</h2>
<p class="sec-sub">从全书抽取的核心概念，每个词条给出蒸馏定义、出处与关联。</p>
<div class="concept-grid">{concept_cards}</div>
<p style="margin-top:18px"><a href="{base}concepts/index.html" style="color:var(--r-blue);font-weight:600">查看全部 {len(CONCEPTS)} 个概念 →</a></p></div></section>
<section class="section"><div class="wrap">
<h2>随书工具</h2>
<p class="sec-sub">附录 A 的实操工具，改写为可勾选、可打印的清单页。</p>
<div class="tool-grid">{tool_cards}</div></div></section>
<section class="section tint"><div class="wrap">
<h2>实战项目轨：AI 组织变革方案</h2>
<p class="sec-sub">笔记轨的毕业设计——同一套方法论落到一个真实业务域：Momcozy 品牌域的 AI Native 实战案例。全部为设计基线，不构成业务授权。</p>
<div class="cta-grid">{practice_html}</div>
<p style="margin-top:14px;font-size:13px;color:#8a97a8">站内可视化：<a href="{base}orgmap.html" style="color:var(--r-blue)">组织与价值流一张图</a>（静态交互版）；外部交互原型：<a href="https://native.sagegogo.com/src/orgmap/" target="_blank" rel="noopener" style="color:var(--r-blue)">三宝 · 3D 组织与经营空间 ↗</a>——50 个数字员工工位 × 20 个天幕业务节点 × 38 条跨层光柱的设计态原型（外部项目门户 · 生产权限 0/53 · 非运行系统）。</p></div></section>"""
    return page_shell("首页", base, "index", f"<main>{body}</main>",
                      "四本书深度解读 + AI Native 组织变革方案实战化公开版")


_NO2SLUG = {c["no"]: c["slug"] for c in CHAPTERS}


def _from_html(label: str, base: str) -> str:
    m = re.match(r"第\s*(\d+)\s*章", label)
    if m:
        slug = _NO2SLUG.get(m.group(1).zfill(2))
        if slug:
            return f'<a href="{base}chapters/{slug}.html">{escape(label)}</a>'
    special = {"序章": "prologue", "终章": "epilogue"}
    if label in special:
        return f'<a href="{base}chapters/{special[label]}.html">{escape(label)}</a>'
    if label.startswith("附录"):
        return f'<a href="{base}tools/index.html">{escape(label)}</a>'
    return escape(label)


def render_concepts(base: str) -> str:
    cards = []
    for c in CONCEPTS:
        rel = "、".join(
            next((x["term"] for x in CONCEPTS if x["slug"] == r), r)
            for r in c.get("related", [])[:4])
        frm = "、".join(_from_html(x, base) for x in c.get("from", []))
        cards.append(
            f'<section class="concept-card" id="{c["slug"]}" style="scroll-margin-top:90px">'
            f'<h3>{escape(c["term"])}</h3><p>{escape(c["definition"])}</p>'
            f'<div class="from">出处：{frm}'
            + (f' · 相关：{escape(rel)}' if rel else '') + '</div></section>')
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span><span>概念索引</span></div>'
        '<div class="cat">CONCEPTS</div><h1>概念索引</h1>'
        f'<p class="sub">从全书蒸馏出的 {len(CONCEPTS)} 个核心概念。词条为原创概括，非原书定义原文。</p>'
        f'<div class="concept-grid" style="margin-top:26px">{"".join(cards)}</div>')
    return page_shell("概念索引", base, "concepts", inner, "AI Native 组织核心概念索引")


def render_tool_page(t: dict, base: str) -> str:
    items = []
    for i, it in enumerate(t["items"], 1):
        q = it["q"] if isinstance(it, dict) else it
        why = it.get("why", "") if isinstance(it, dict) else ""
        why_html = f'<span class="why">{escape(why)}</span>' if why else ""
        items.append(f'<li><input type="checkbox" id="t{i}"><label for="t{i}"><span class="q">{i}. {inline(q)}</span>{why_html}</label></li>')
    checklist = (
        f'<div class="checklist" data-tool="{t["slug"]}" id="tool-{t["slug"]}">'
        '<div class="chk-head"><b><span data-count>0 / ' + str(len(items)) + '</span> 已勾选</b>'
        '<span><button type="button" data-reset>重置</button> <button type="button" data-print>打印</button></span></div>'
        f'<ol>{"".join(items)}</ol>'
        f'<div class="chk-foot">勾选状态保存在本机浏览器（localStorage），刷新不丢。来源：{escape(t.get("source", "附录A"))}。</div></div>')
    inner = (
        f'<div class="crumb"><a href="{base}index.html">全书地图</a><span>/</span>'
        f'<a href="{base}tools/index.html">随书工具</a><span>/</span><span>工具 {t["idx"]}</span></div>'
        f'<div class="cat">TOOL {t["idx"]:02d}</div><h1>{escape(t["name"])}</h1>'
        f'<p class="lead">{inline(t.get("desc", ""))}</p>'
        + checklist
        + ('<div class="note" style="margin-top:26px">' + inline(t["note"]) + '</div>' if t.get("note") else "")
    )
    return reader_page(base, "", inner, [], f'工具{t["idx"]} {t["name"]}',
                       t.get("desc", "")[:120], nav_current="tools")


def render_tools_index(base: str) -> str:
    cards = "".join(
        f'<div class="tool-card"><span class="idx">TOOL {t["idx"]:02d}</span><h3>{escape(t["name"])}</h3>'
        f'<p>{escape(t["desc"])}</p><span style="font-size:12px;color:#8a97a8">{len(t["items"])} 项 · {escape(t.get("source", ""))}</span>'
        f'<a class="go" href="{base}tools/{t["slug"]}.html">打开工具 →</a></div>'
        for t in TOOLS)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span><span>随书工具</span></div>'
        '<div class="cat">TOOLS</div><h1>随书工具箱</h1>'
        '<p class="sub">附录 A 的五件实操工具加转型日历，改写为可勾选清单。清单类内容属事实性资料，尽量保留原表项目；每项补充了「它在防什么 / 合格证据」的说明。</p>'
        f'<div class="tool-grid" style="margin-top:26px">{cards}</div>')
    return page_shell("随书工具", base, "tools", inner, "AI Native 组织随书工具清单")


def render_terms(base: str) -> str:
    groups = []
    for g in TERMS:
        rows = "".join(
            f'<tr><td class="term-name"><code>{escape(it["term"])}</code></td>'
            f'<td>{inline(it["desc"])}</td></tr>'
            for it in g["items"])
        groups.append(
            f'<section class="term-group"><h2>{escape(g["group"])}</h2>'
            f'<div class="table-wrap"><table class="terms"><tbody>{rows}</tbody></table></div></section>')
    n = sum(len(g["items"]) for g in TERMS)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span><span>方案术语表</span></div>'
        '<div class="cat">GLOSSARY</div><h1>方案术语表</h1>'
        f'<p class="sub">各篇「实践映射」中出现的内部项目代号与术语，共 {n} 条，按决策编号、岗位契约、Case 协同、治理执行、平台组织五组整理。术语以本站姊妹项目《AI 组织变革方案》的决策记录（D-020~D-053）为准。</p>'
        '<div style="margin-top:26px">' + "".join(groups) + '</div>')
    return page_shell("方案术语表", base, "terms", inner,
                      "AI 组织变革方案内部术语表")


def render_pilot(base: str) -> str:
    blocks = PILOT["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span><span>从书到试点</span></div>'
        '<div class="cat">BRIDGE</div>'
        f'<h1>{escape(PILOT["title"])}</h1>'
        f'<p class="lead">{inline(PILOT.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>性质 <b>本站原创 · 非原书内容</b></span>'
        f'<span>约 <b>{PILOT.get("minutes", "20")}</b> 分钟读完</span>'
        '<span>用途 <b>试点设计前的操作序列</b></span></div></div>'
        + body_html)
    return reader_page(base, "", inner, heads, PILOT["title"],
                       PILOT.get("lead", "")[:120], nav_current="pilot")


def render_brand_plan(base: str) -> str:
    blocks = BRAND_PLAN["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span>'
        '<a href="' + base + 'pilot.html">从书到试点</a><span>/</span><span>品牌域实战路线图</span></div>'
        '<div class="cat">ROLLOUT</div>'
        f'<h1>{escape(BRAND_PLAN["title"])}</h1>'
        f'<p class="lead">{inline(BRAND_PLAN.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>性质 <b>设计基线 · 无生产授权</b></span>'
        f'<span>约 <b>{escape(BRAND_PLAN.get("minutes", "18"))}</b> 分钟读完</span>'
        '<span>权威版 <b>姊妹仓库 FLOW-09-ROLLOUT-ROADMAP</b></span></div></div>'
        + body_html)
    return reader_page(base, "", inner, heads, BRAND_PLAN["title"],
                       BRAND_PLAN.get("lead", "")[:120], nav_current="brand-plan")


def render_orgmap(base: str) -> str:
    om = ORGMAP
    roles = {r["id"]: r for r in om["roles"]}
    bvs = [s for s in om["streams"] if s["family"] == "BVS"]
    cvs = [s for s in om["streams"] if s["family"] == "CVS"]

    def _rlabel(agid: str) -> str:
        r = roles.get(agid)
        return f'{r["alias"]}·{r["title"]}' if r else agid

    def _stream_card(s: dict) -> str:
        meta = f'{_rlabel(s["owner"])} · {len(s["contributors"])} 岗位'
        meta += f' · {len(s["scenarios"])} 场景' if s["scenarios"] else ' · 无业务场景'
        return (
            f'<button type="button" class="om-stream om-{s["family"].lower()}" '
            f'data-om="stream:{escape(s["key"])}" title="{escape(s["title"])}">'
            f'<span class="om-sid">{escape(s["key"])}<i>{escape(s["sid"])}</i></span>'
            f'<b>{escape(s["title"])}</b>'
            f'<span class="om-meta">{escape(meta)}</span></button>')

    def _scn_chip(s: dict) -> str:
        return (f'<button type="button" class="om-scn" data-om="scn:{escape(s["id"])}">'
                f'<b>{escape(s["id"])}</b><span>{escape(s["title"])}</span></button>')

    def _role_chip(r: dict) -> str:
        return (f'<button type="button" class="om-role" data-om="role:{escape(r["id"])}" '
                f'title="{escape(r["id"] + " · " + r["title"])}">'
                f'<b>{escape(r["alias"])}</b><span>{escape(r["title"])}</span></button>')

    plane_blocks = []
    for p in om["planes"]:
        members = [r for r in om["roles"] if r["plane"] == p["id"]]
        chips = "".join(_role_chip(r) for r in members)
        plane_blocks.append(
            f'<div class="om-plane" data-om="plane:{escape(p["id"])}" '
            f'title="{escape(p["name"])} · 点击查看平面职责与契约">'
            f'<div class="om-plane-h"><b>{escape(p["name"])}</b>'
            f'<i>{p["role_count"]} 个岗位</i></div>'
            f'<p class="om-plane-purpose">{escape(p["purpose"])}</p>'
            f'<div class="om-roles">{chips}</div></div>')

    badges = [
        ("ok", "岗位契约", "50/50 · 五契约蓝图态"),
        ("ok", "价值流", "13 条 · 场景 20/20 v1"),
        ("warn", "生产权限", "0 · 无运行实例"),
        ("warn", "试点门禁", "PILOT-G1 未就绪"),
        ("", "视觉身份", "53 绑定 · 运行影响 0"),
    ]
    badge_html = "".join(
        f'<span class="om-badge {cls}"><b>{escape(k)}</b>{escape(v)}</span>'
        for cls, k, v in badges)

    embed = {k: om[k] for k in ("planes", "plane_contracts", "streams", "scenarios", "roles")}
    om_json = json.dumps(embed, ensure_ascii=False).replace("</", "<\\/")
    map_html = f'''
<div class="om-app" id="om-app">
<p class="om-hint">点选任意节点（价值流 / 场景 / 岗位 / 平面）查看绑定关系——高亮为直接绑定，淡出为无关；再点一次或按 Esc 清除。</p>
<div class="om-badges">{badge_html}</div>
<section class="om-band" aria-label="价值流">
<h3 class="om-band-t">业务天空 · 价值流 <small>9 条业务经营流 BVS + 4 条能力供应流 CVS · 每条流一个 AI 结果负责人</small></h3>
<div class="om-streams om-bvs">{"".join(_stream_card(s) for s in bvs)}</div>
<div class="om-streams om-cvs">{"".join(_stream_card(s) for s in cvs)}</div>
</section>
<section class="om-band" aria-label="业务场景">
<h3 class="om-band-t">场景带 · 20 个业务场景 <small>一张 Case 只绑定一条主流与一个主场景（D-025）</small></h3>
<div class="om-scns">{"".join(_scn_chip(s) for s in om["scenarios"])}</div>
</section>
<section class="om-band" aria-label="AI岗位">
<h3 class="om-band-t">员工工位 · 四平面 50 个 AI 岗位 <small>D-021 逻辑责任分类 · 非行政层级 / 运行实例 / 权限</small></h3>
<div class="om-planes">{"".join(plane_blocks)}</div>
</section>
<div class="om-drawer" id="om-drawer" aria-live="polite">
<div class="om-drawer-in"><h4>选择一个节点</h4>
<p>点击上方面板中的价值流、场景、岗位或平面，这里会显示它的职责、边界与全部绑定对象——清单中的条目可以继续点选跳转。</p>
<p class="om-drawer-links">延伸阅读：<a href="{base}pilot-assets.html">试点资产地图</a> · <a href="{base}brand-plan.html">实战路线图</a> · <a href="https://native.sagegogo.com/src/orgmap/" target="_blank" rel="noopener">3D 组织空间 ↗</a></p></div>
</div>
</div>
<script type="application/json" id="om-data">{om_json}</script>'''

    blocks = om["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = [("sec-map", "组织与价值流全景图")] + chapter_headings(blocks)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span>'
        '<a href="' + base + 'pilot.html">从书到试点</a><span>/</span><span>组织与价值流一张图</span></div>'
        '<div class="cat">ORG MAP</div>'
        f'<h1>{escape(om["title"])}</h1>'
        f'<p class="lead">{inline(om.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>性质 <b>设计基线 · 无生产授权</b></span>'
        '<span>规模 <b>50 岗位 · 13 价值流 · 20 场景</b></span>'
        f'<span>约 <b>{escape(om.get("minutes", "12"))}</b> 分钟读完</span>'
        '<span>交互 <b>点选节点查看绑定</b></span></div></div>'
        + map_html + body_html)
    return reader_page(base, "", inner, heads, om["title"],
                       om.get("lead", "")[:120], nav_current="orgmap")


def sidebar_html_product(base: str) -> str:
    """Left directory for the Sage product page: overview + scene classes."""
    cat = PRODUCT["catalog"]
    out = ['<aside class="dir" aria-label="Sage 产品目录">',
           '<div class="dir-search"><label for="dir-search">搜索目录</label>',
           '<input id="dir-search" type="search" placeholder="场景、工作、工具…" autocomplete="off"></div>']
    out.append('<div class="dir-group"><h4>概览</h4>')
    for hid, label, hay in [
            ("pd-positioning", "定位与客户", "定位 客户 成长线 覆盖范围"),
            ("pd-products", "产品组合", "产品 sage 单点工具 四档"),
            ("pd-structure", "Sage 结构", "结构 场景统计 交付方式")]:
        out.append(f'<a href="#{hid}" data-search="{escape(hay, quote=True)}">{escape(label)}</a>')
    out.append('</div><div class="dir-group"><h4>经营场景 · 10 类</h4>')
    for sc in cat["scenes"]:
        hay = f'{sc["id"]} {sc["name"]} 细分场景'
        out.append(f'<a href="#pd-{sc["id"].lower()}" data-search="{escape(hay, quote=True)}">'
                   f'<span class="no">{sc["id"]}</span>{escape(sc["name"])}</a>')
    out.append('</div><div class="dir-group"><h4>平台运营 · 4 类</h4>')
    for i, pf in enumerate(cat["platforms"]):
        out.append(f'<a href="#pd-plt-{i}" data-search="{escape(pf["name"], quote=True)} 细分场景">'
                   f'<span class="no">{i + 1}</span>{escape(pf["name"])}</a>')
    out.append('</div><div class="dir-group"><h4>标杆 · 主线 · 工具</h4>')
    for hid, label, hay in [
            ("pd-bench", "两个标杆场景", "标杆 shopify 自动运营 voc 洞察"),
            ("pd-lines", "七条主线", "主线 上新线 口碑线 机会线 经营线 品牌线 复购线 新平台线"),
            ("pd-tools", "单点工具", "工具 合规审核 数据采集 视频分镜")]:
        out.append(f'<a href="#{hid}" data-search="{escape(hay, quote=True)}">{escape(label)}</a>')
    out.append('</div><p class="dir-empty" hidden>没有匹配的目录项。</p></aside>')
    return "".join(out)


def _pchip(w: dict) -> str:
    cls = ' class="pchip ref"' if w.get("ref") else ' class="pchip"'
    mode = f'<i>{escape(w["mode"])}</i>' if w.get("mode") else ""
    pf = f'<em>{escape(w["platform"])}</em>' if w.get("platform") else ""
    return f'<span{cls}>{escape(w["name"])}{mode}{pf}</span>'


def _scene_table(subs: list) -> str:
    rows = []
    for sub in subs:
        works = "".join(_pchip(w) for w in sub["works"])
        rows.append(
            f'<tr><td class="psc"><b>{escape(sub["id"])} {escape(sub["name"])}</b></td>'
            f'<td>{escape(sub["question"])}</td>'
            f'<td class="psw">{works}</td>'
            f'<td>{escape(sub["result"])}</td></tr>')
    return ('<div class="table-wrap"><table><thead><tr>'
            '<th>细分场景</th><th>要回答的问题</th><th>包含的工作</th><th>交到客户手里的结果</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def _simple_table(head: list, rows: list) -> str:
    h = "".join(f"<th>{escape(c)}</th>" for c in head)
    r = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table></div>'


def _flow(text: str) -> str:
    steps = [x.strip() for x in text.split("→") if x.strip()]
    body = '<span class="pflow-arrow">→</span>'.join(
        f'<span class="pstep">{escape(x)}</span>' for x in steps)
    return f'<div class="pflow">{body}</div>'


def render_product(base: str) -> str:
    P = PRODUCT
    pos = P["positioning"]
    heads: list[tuple[str, str]] = []
    parts: list[str] = []

    def h2(hid: str, title: str) -> None:
        heads.append((hid, title))
        parts.append(f'<h2 id="{hid}"><span class="sec-no">{len(heads):02d}</span>{escape(title)}</h2>')

    def h3(hid: str, title: str) -> None:
        heads.append((hid, title))
        parts.append(f'<h3 id="{hid}">{escape(title)}</h3>')

    # ---- 01 定位与客户 ----
    h2("pd-positioning", "定位与客户")
    parts.append(f'<p class="lead">{escape(pos["promise"])}</p>')
    cust = "".join(
        f'<div class="path-card"><h4>{escape(c["name"])}</h4><p>{escape(c["desc"])}</p>'
        f'<p style="margin-top:8px"><b>最先需要：</b>{escape(c["need"])}</p></div>'
        for c in pos["customers"])
    parts.append(f'<div class="path-grid" style="grid-template-columns:repeat(2,minmax(0,1fr))">{cust}</div>')
    parts.append(f'<p style="margin:18px 0 8px"><b>同一条成长线</b> · {escape(pos["growth_note"])}</p>')
    grow = '<span class="pgrow-arrow">→</span>'.join(
        f'<span class="pstep">{escape(x)}</span>' for x in pos["growth_line"])
    parts.append(f'<div class="pflow pgrow">{grow}</div>')
    parts.append("<h3>覆盖范围</h3>")
    parts.append("<ul>" + "".join(f"<li>{escape(x)}</li>" for x in pos["scope"]) + "</ul>")

    # ---- 02 产品组合 ----
    h2("pd-products", "产品组合")
    parts.append(f'<p>{escape(P["products"]["lead"])}</p>')
    m = P["products"]["matrix"]
    mrows = []
    for row in m["rows"]:
        label, cells = row[0], row[1:]
        mrows.append("<tr><td><b>" + escape(label) + "</b></td>" +
                     "".join(f"<td>{escape(c)}</td>" for c in cells) + "</tr>")
    mh = "".join(f"<th>{escape(c)}</th>" for c in m["head"])
    parts.append('<div class="table-wrap"><table><thead><tr>' + mh +
                 f'</tr></thead><tbody>{"".join(mrows)}</tbody></table></div>')
    t = P["products"]["tiers"]
    parts.append("<h3>按预算分四档购买</h3>")
    parts.append(f'<p>{escape(t["lead"])}</p>')
    parts.append(_simple_table(t["head"], t["rows"]))
    parts.append("<h3>贯穿四档的三条原则</h3>")
    parts.append('<div class="path-grid" style="grid-template-columns:repeat(3,minmax(0,1fr))">' + "".join(
        f'<div class="path-card"><h4>{escape(n)}</h4><p>{escape(d)}</p></div>'
        for n, d in P["products"]["principles"]) + "</div>")

    # ---- 03 Sage 结构 ----
    h2("pd-structure", "Sage 的结构")
    st = P["structure"]
    parts.append(f'<p>{escape(st["lead"])}</p>')
    parts.append(f'<p class="note">{escape(st["modes"])}</p>')
    parts.append(_simple_table(st["summary_rows"][0], st["summary_rows"][1:]))

    # ---- 04 经营场景明细 ----
    h2("pd-scenes", "经营场景明细")
    parts.append("<p>10 类场景、37 个细分场景，各平台通用。每个细分场景只回答一个问题、有一个主要使用人、交付客户能验收的结果，并尽量走完同一个闭环：发现 → 判断 → 出稿 → 客户确认 → 回看结果。</p>")
    parts.append('<p style="font-size:12.5px;color:var(--r-faint)">标记说明：<b>例行</b>=定时自动运行；<b>项目</b>=多项工作串成一个完整结果；无标记=交办一次、交付一次；平台名标签=只适用该平台，未标的各平台通用；虚线框=登记在其他细分场景的引用工作。</p>')
    for sc in P["catalog"]["scenes"]:
        h3(f'pd-{sc["id"].lower()}', f'{sc["id"]} {sc["name"]}')
        parts.append(f'<p class="psc-desc">{escape(sc["desc"])}</p>')
        parts.append(_scene_table(sc["subs"]))

    # ---- 05 平台运营明细 ----
    h2("pd-platforms", "平台运营明细")
    parts.append("<p>只在某个平台存在的工作，以及多平台同时经营时的协同。通用工作（商品资料、客服、复盘等）不在这里重复，以虚线标签表示引用。</p>")
    for i, pf in enumerate(P["catalog"]["platforms"]):
        h3(f'pd-plt-{i}', pf["name"])
        parts.append(f'<p class="psc-desc">{escape(pf["desc"])}</p>')
        parts.append(_scene_table(pf["subs"]))

    # ---- 06 两个标杆 ----
    h2("pd-bench", "两个标杆场景")
    bm = P["benchmarks"]
    h3("pd-bench-m", bm["matrix_title"])
    parts.append(f'<p>{escape(bm["matrix_desc"])}</p>')
    mrows = []
    for r in bm["matrix"]:
        works = "".join(_pchip({**w, "ref": False}) for w in r["works"])
        role = f'<b>{escape(r["role"])}</b>' if r["role"] else ""
        mrows.append(f'<tr><td class="psc">{role}</td><td class="psc">{escape(r["ring"])}</td>'
                     f'<td class="psw">{works}</td></tr>')
    parts.append('<div class="table-wrap"><table><thead><tr><th>岗位</th><th>Shopify 运营环节</th>'
                 f'<th>负责的工作</th></tr></thead><tbody>{"".join(mrows)}</tbody></table></div>')
    parts.append(f'<p class="note">{escape(bm["matrix_why"])}</p>')
    h3("pd-bench-v", bm["voc_title"])
    parts.append(f'<p>{escape(bm["voc_desc"])}</p>')
    vrows = []
    for v in bm["voc"]:
        mode = f' <i>{escape(v["mode"])}</i>' if v.get("mode") else ""
        vrows.append(f'<tr><td class="psc"><b>{escape(v["work"])}{mode}</b></td><td>{escape(v["answer"])}</td></tr>')
    parts.append('<div class="table-wrap"><table><thead><tr><th>工作</th><th>回答什么</th></tr></thead>'
                 f'<tbody>{"".join(vrows)}</tbody></table></div>')
    parts.append(f'<p class="note">{escape(bm["voc_why"])}</p>')
    parts.append("<h3>两个标杆之间的关系</h3>")
    parts.append('<div class="path-grid" style="grid-template-columns:repeat(2,minmax(0,1fr))">' + "".join(
        f'<div class="path-card"><h4>{escape(n)}</h4><p>{escape(d)}</p></div>'
        for n, d in bm["relation"]) + "</div>")

    # ---- 07 七条主线 ----
    h2("pd-lines", "七条主线")
    ln = P["lines"]
    parts.append(f'<p>{escape(ln["lead"])}</p>')
    parts.append('<div class="pline-grid">' + "".join(
        f'<div class="path-card pline"><h4>{escape(n)}</h4><p>{escape(d)}</p>{_flow(f)}</div>'
        for n, d, f in ln["items"]) + "</div>")
    parts.append("<h3>关键交接</h3>")
    parts.append(_simple_table(["交接", "规则"], ln["handoffs"]))

    # ---- 08 单点工具 ----
    h2("pd-tools", "单点工具")
    parts.append("<p>三个工具只对「这一件结果」负责，不需要了解客户的店铺和经营情况就能用。</p>")
    for i, tl in enumerate(P["tools"]):
        h3(f'pd-tool-{i}', tl["name"])
        parts.append(f'<p><b>问题：</b>{escape(tl["problem"])}</p>')
        kv = [("谁来买", tl["buyer"]), ("客户给什么", tl["input"]),
              ("客户拿到什么", tl["output"]), ("怎么验收", tl["verify"]),
              ("怎么买", tl["buy"]), ("不做什么", tl["wont"])]
        parts.append('<div class="table-wrap"><table><tbody>' + "".join(
            f'<tr><td class="psc"><b>{escape(k)}</b></td><td>{escape(v)}</td></tr>'
            for k, v in kv) + "</tbody></table></div>")
        if tl.get("in_sage"):
            parts.append("<h4 class='map-h4' style='margin:14px 0 6px'>在 Sage 里出现在哪</h4>")
            parts.append('<div class="table-wrap"><table><tbody>' + "".join(
                f'<tr><td class="psc">{escape(a)}</td><td>{escape(b)}</td></tr>'
                for a, b in tl["in_sage"]) + "</tbody></table></div>")
        parts.append(f'<p class="note"><b>单买与在 Sage 里用的区别：</b>{escape(tl["upgrade"])}</p>')

    # ---- 边界 ----
    parts.append('<div class="note"><b>边界声明：</b>本页为产品层规划 v5（2026-11-23）的公开呈现，全部能力为设计状态，不构成已上线产品、性能承诺或业务授权。对外动作（发布、提交、退款、投诉）始终由客户执行。</div>')

    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">首页</a><span>/</span><span>Sage 产品</span></div>'
        '<div class="cat">PRODUCT · SAGE</div>'
        f'<h1>{escape(P["title"])}</h1>'
        f'<p class="lead">{inline(P.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>版本 <b>{escape(P.get("version", ""))}</b></span>'
        '<span>性质 <b>规划文档 · 设计状态</b></span>'
        f'<span>规模 <b>52 细分场景 · 117 项工作</b></span>'
        f'<span>约 <b>{escape(P.get("minutes", "25"))}</b> 分钟读完</span></div></div>'
        + "".join(parts))
    return reader_page(base, "", inner, heads, P["title"],
                       P.get("lead", "")[:120], nav_current="product",
                       sidebar=sidebar_html_product(base))


def render_sitemap(base: str) -> str:
    blocks = SITEMAP["sections"]
    counters = {"h2": 0, "h3": 0}
    body_html = render_blocks(blocks, base, counters)
    heads = chapter_headings(blocks)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span><span>站点地图</span></div>'
        '<div class="cat">GUIDE</div>'
        f'<h1>{escape(SITEMAP["title"])}</h1>'
        f'<p class="lead">{inline(SITEMAP.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        '<span>性质 <b>本站原创导览 · 非原书内容</b></span>'
        f'<span>约 <b>{escape(SITEMAP.get("minutes", "6"))}</b> 分钟读完</span>'
        '<span>覆盖 <b>全站 12 个板块</b></span></div></div>'
        + body_html)
    return reader_page(base, "", inner, heads, SITEMAP["title"],
                       SITEMAP.get("lead", "")[:120], nav_current="sitemap")


def render_semantic(base: str) -> str:
    groups = []
    for g in SEMANTIC["groups"]:
        rows = "".join(
            f'<tr><td class="term-name"><code>{escape(it["id"])}</code></td>'
            f'<td><strong>{escape(it["name"])}</strong><br><span style="color:#5b6b7d">{inline(it["desc"])}</span></td>'
            f'<td style="white-space:nowrap;font-size:12.5px;color:#8a97a8">{escape(it.get("meta", ""))}'
            + (f'<br><a href="{escape(it["link"], quote=True)}" target="_blank" rel="noopener" style="color:#4a6fa5">权威版 ↗</a>' if it.get("link") else "")
            + '</td></tr>'
            for it in g["items"])
        groups.append(
            f'<section class="term-group"><h2>{escape(g["group"])} · {len(g["items"])}</h2>'
            f'<div class="table-wrap"><table class="terms"><tbody>{rows}</tbody></table></div></section>')
    kpis = "".join(
        f'<div class="kpi"><b>{escape(v)}</b><span>{escape(l)}</span></div>' for v, l in SEMANTIC["kpis"])
    d = SEMANTIC["disambig"]
    drows = "".join(
        f'<tr><td><strong>{escape(r[0])}</strong></td><td>{inline(r[1])}</td><td>{inline(r[2])}</td></tr>'
        for r in d["rows"])
    prows = "".join(
        f'<tr><td><strong>{escape(p["item"])}</strong><br><span style="color:#8a97a8;font-size:12.5px">{inline(p["blocker"])}</span></td>'
        f'<td style="font-size:13px;color:#5b6b7d">{inline(p["note"])}</td></tr>'
        for p in SEMANTIC["pending"])
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span>'
        '<a href="' + base + 'pilot.html">从书到试点</a><span>/</span><span>语义底座</span></div>'
        '<div class="cat">SEMANTIC LAYER</div><h1>' + escape(SEMANTIC["title"]) + '</h1>'
        f'<p class="lead">{inline(SEMANTIC.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>状态 <b>{escape(SEMANTIC.get("status", ""))}</b></span>'
        f'<span>交付物 <b>{sum(len(g["items"]) for g in SEMANTIC["groups"])} 项</b></span>'
        f'<span>约 <b>{escape(SEMANTIC.get("minutes", "10"))}</b> 分钟读完</span></div></div>'
        f'<div class="kpi-strip" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0">{kpis}</div>'
        '<div style="margin-top:26px">' + "".join(groups) + '</div>'
        '<section class="term-group"><h2>高频口径速查 · 消歧对照</h2>'
        '<div class="table-wrap"><table class="terms"><thead><tr>'
        + "".join(f'<th>{escape(h)}</th>' for h in d["head"])
        + f'</tr></thead><tbody>{drows}</tbody></table></div></section>'
        '<section class="term-group"><h2>待数据激活清单 · pending_data</h2>'
        '<p style="font-size:13.5px;color:#5b6b7d;margin:0 0 10px">以下项目全部以占位符存在，G1 数据就绪后回填并产出事理规则 v0——这是语义层从「设计基线」到「影子运行输入」的最后一公里。</p>'
        '<div class="table-wrap"><table class="terms"><tbody>' + prows + '</tbody></table></div></section>'
        '<div class="note" style="margin-top:26px"><strong>接线状态：</strong>' + inline(SEMANTIC.get("wiring", "")) + '<br><br>'
        + inline(SEMANTIC.get("boundary", "")) + '</div>')
    return page_shell("语义底座 v0 全景", base, "semantic", inner,
                      "语义底座 v0：48 术语/20 对象 34 关系/38 契约规则/24 权限四元组")


def render_g1_pack(base: str) -> str:
    G = G1_PACK
    counters = {"h2": 0, "h3": 0}
    body = render_blocks(G["blocks"], base, counters)
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span>'
        '<a href="' + base + 'pilot.html">从书到试点</a><span>/</span><span>数据就绪交付包</span></div>'
        '<div class="cat">G1 DATA PACK</div><h1>' + escape(G["title"]) + '</h1>'
        f'<p class="lead">{inline(G.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>状态 <b>{escape(G.get("status", ""))}</b></span>'
        f'<span>约 <b>{escape(G.get("minutes", "8"))}</b> 分钟读完</span></div></div>'
        '<div style="margin-top:26px">' + body + '</div>'
        '<div class="note" style="margin-top:26px">' + inline(G.get("boundary", "")) + '</div>')
    return page_shell("数据就绪交付包", base, "g1-pack", inner,
                      "数据就绪交付包：AI 组织落地的企业侧取数框架——三层验收、六件交付物、证据六要件与 PII 边界")


def render_pilot_assets(base: str) -> str:
    groups = []
    for g in PILOT_ASSETS["groups"]:
        rows = "".join(
            f'<tr><td class="term-name"><code>{escape(it["id"])}</code></td>'
            f'<td><strong>{escape(it["name"])}</strong><br><span style="color:#5b6b7d">{inline(it["desc"])}</span></td>'
            f'<td style="white-space:nowrap;font-size:12.5px;color:#8a97a8">{escape(it.get("meta", ""))}'
            + (f'<br><a href="{escape(it["link"], quote=True)}" target="_blank" rel="noopener" style="color:#4a6fa5">规格 ↗</a>' if it.get("link") else "")
            + '</td></tr>'
            for it in g["items"])
        paged = (f' class="paginated" data-page-size="{g["paginate"]}"'
                 if g.get("paginate") else "")
        groups.append(
            f'<section class="term-group"><h2>{escape(g["group"])} · {len(g["items"])}</h2>'
            f'<div class="table-wrap"><table class="terms"{paged}><tbody>{rows}</tbody></table></div></section>')
    n = sum(len(g["items"]) for g in PILOT_ASSETS["groups"])
    inner = (
        '<div class="crumb"><a href="' + base + 'index.html">全书地图</a><span>/</span>'
        '<a href="' + base + 'pilot.html">从书到试点</a><span>/</span><span>品牌域试点资产</span></div>'
        '<div class="cat">PILOT ASSETS</div><h1>' + escape(PILOT_ASSETS["title"]) + '</h1>'
        f'<p class="lead">{inline(PILOT_ASSETS.get("lead", ""))}</p>'
        '<div class="page-head" style="padding:0 0 8px"><div class="facts">'
        f'<span>状态 <b>{escape(PILOT_ASSETS.get("status", ""))}</b></span>'
        f'<span>资产 <b>{n} 项</b></span>'
        f'<span>约 <b>{escape(PILOT_ASSETS.get("minutes", "10"))}</b> 分钟读完</span></div></div>'
        '<div style="margin-top:26px">' + "".join(groups) + '</div>'
        '<div class="note" style="margin-top:26px">' + inline(PILOT_ASSETS.get("boundary", "")) + '</div>')
    return page_shell("品牌域试点资产地图", base, "pilot-assets", inner,
                      "品牌域试点资产地图：FLOW-09 价值流、场景规格、Skill 契约、双层 KPI 与首个 Case 章程")


def render_about(base: str) -> str:
    inner = f"""
<div class="crumb"><a href="{base}index.html">全书地图</a><span>/</span><span>关于</span></div>
<div class="cat">ABOUT</div><h1>关于本站</h1>
<p class="lead">本仓库是《{escape(BOOK['title'])}》的个人深度解读笔记，目标是把书中的框架萃取成可检索、可对照、可执行的知识，而不是复制原书。</p>
<h2 id="s-about-1">内容政策</h2>
<ul>
<li><strong>解读为主：</strong>章节内容为原创蒸馏重写，保留原书论证结构；短引用单处不超过 80 字并标注页码。</li>
<li><strong>插图：</strong>书中插图均为 PDF 矢量绘制；本站按图号裁剪导出 WebP，每幅标注原书页码。</li>
<li><strong>工具：</strong>附录清单属事实性资料，尽量保留原表项目并补充说明。</li>
<li><strong>变革手记：</strong>只做要点提炼，不转载原文。</li>
</ul>
<h2 id="s-about-2">版权说明</h2>
<p>原书 © {escape(BOOK['author'])}，{escape(BOOK['publisher'])} 出版，ISBN {escape(BOOK['isbn'])}。本站内容仅供个人精读与小范围分享；如需公开传播，请先获得著作权人许可。本站不主张对原书文字与插图的权利。</p>
<h2 id="s-about-3">第二本书说明</h2>
<p>《{escape(BOOK2["title"])}》（{escape(BOOK2["author"])} 著，{escape(BOOK2["publisher"])}，ISBN {escape(BOOK2["isbn"])}）为扫描影印版 PDF，无正式文本层。本站对其采用「全书地图 + 战略章节精读」结构：25 章框架索引基于 OCR 辅助精读，引用页码以原书为准、短语以扫描页核对为准；8 篇精读为原创蒸馏重写，与第一本书同一内容政策。两书整合见<a href="{base}synthesis.html">两书合璧</a>页。</p>
<h2 id="s-about-4">实践映射说明</h2>
<p>每篇解读末尾的「实践映射」将书中框架对照作者本人的 AI 组织变革设计项目（约 50 个 AI 岗位、八阶段协同、Policy Gate 授权体系、FLOW-09 品牌资产经营），属于本站原创的二次创作，与原书作者无关。</p>
<h2 id="s-about-5">技术</h2>
<p>纯静态站：Python 标准库构建（<code>build.py</code>），无前端框架与构建依赖；内容为 JSON 数据，页面为构建期渲染的 HTML；交互（目录筛选、本页目录、工具勾选）为渐进增强，不影响无 JS 阅读。</p>"""
    return page_shell("关于本站", base, "about", inner, "关于本站与引用规范")
