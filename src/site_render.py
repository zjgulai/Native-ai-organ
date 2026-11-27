"""Rendering primitives: inline md-lite, content blocks, figures, page chrome.

All functions return HTML strings; data comes from site_data.
"""
from __future__ import annotations

import re
from html import escape

from site_data import BOOK, CHAPTERS, CHAPTER_CONTENT, CONCEPTS, TOOLS, BOOK2, BOOK3, BOOK4, BRAND2_CONTENT, BOOK3_CONTENT, BOOK4_CONTENT, AGENT_LAB, STACK, AGENT_PLAYBOOK, AGENT_FIELD
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

BLOCK_TAGS = {"p", "h2", "h3", "quote", "fig", "b4fig", "list", "olist", "table", "note", "map"}


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
        elif kind == "b4fig":
            out.append(render_b4_figure(b["b4fig"], base))
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


def render_b4_figure(f: dict, base: str) -> str:
    """Embed an SVG figure from the open-source book4 repo (Apache-2.0)."""
    fn = f["file"]
    caption = f.get("caption", "")
    src_url = f.get("src", "https://github.com/bojieli/ai-agent-book")
    return (
        f'<figure class="figure"><a href="{base}assets/book4/{fn}" target="_blank" rel="noopener">'
        f'<img src="{base}assets/book4/{fn}" alt="{escape(caption)}" loading="lazy"></a>'
        f'<figcaption>{escape(caption)}<span class="src">摘自《深入理解 AI Agent》配图（Apache-2.0） · '
        f'<a href="{src_url}" target="_blank" rel="noopener">原始 SVG ↗</a></span></figcaption></figure>'
    )


# ------------------------------------------------------------------ chrome


def nav_html(base: str, current: str) -> str:
    """Two-level nav: direct links + grouped dropdowns.

    current = the page's section key; a dropdown parent gets .has-current
    when the current page belongs to its group.
    """
    esc = escape

    def link(href: str, label: str, key: str, is_index_dup: bool = False) -> str:
        # index.html appears twice (top-level 首页 + 书1 dropdown); only the
        # top-level carries aria-current to avoid duplicate page markers.
        cur = ' aria-current="page"' if key == current and not is_index_dup else ""
        return f'<a href="{base}{href}"{cur}>{esc(label)}</a>'

    groups = [
        ("books", "读书笔记", [
            ("组织书 · 书1", [
                ("index.html", "全书地图", "index", True),
                ("chapters/index.html", "章节解读", "chapters", False),
                ("concepts/index.html", "概念索引", "concepts", False),
                ("tools/index.html", "随书工具", "tools", False),
            ]),
            ("品牌书 · 书2", [
                ("brand2/index.html", "弱品牌强品牌", "brand2", False),
            ]),
            ("本体书 · 书3", [
                ("book3/index.html", "本体驱动AI数据管理", "book3", False),
                ("semantic.html", "语义底座", "semantic", False),
            ]),
            ("Agent书 · 书4", [
                ("book4/index.html", "Agent书", "book4", False),
                ("agent-lab.html", "Agent实验场", "agent-lab", False),
                ("experiments.html", "配套实验", "experiments", False),
                ("toyagent-steps.html", "原理文章", "toyagent-steps", False),
                ("agent-playbook/index.html", "Agent Playbook", "agent-playbook", False),
                ("agent-field/index.html", "Field Guide", "agent-field", False),
            ]),
            ("合璧", [
                ("triology.html", "三书合璧", "triology", False),
                ("synthesis.html", "两书合璧", "synthesis", False),
                ("stack.html", "四层架构", "stack", False),
            ]),
        ]),
        ("practice", "实战方案", [
            (None, [
                ("pilot.html", "从书到试点", "pilot", False),
                ("pilot-assets.html", "试点资产", "pilot-assets", False),
                ("g1-pack.html", "G1 交付包", "g1-pack", False),
                ("brand-plan.html", "实战路线", "brand-plan", False),
                ("orgmap.html", "组织图", "orgmap", False),
            ]),
        ]),
        ("site", "站点", [
            (None, [
                ("sitemap.html", "导览", "sitemap", False),
                ("terms.html", "术语表", "terms", False),
                ("about.html", "关于", "about", False),
            ]),
        ]),
    ]

    def group_html(gid: str, glabel: str, sections: list) -> str:
        keys = {k for _, links in sections for _, _, k, _ in links}
        has_cur = current in keys
        parts = []
        for slabel, links in sections:
            if slabel:
                parts.append(f'<p class="nav-drop-label">{esc(slabel)}</p>')
            parts.extend(link(h, l, k, d) for h, l, k, d in links)
        return (
            f'<div class="nav-group nav-group-{gid}{" has-current" if has_cur else ""}">'
            f'<button type="button" class="nav-group-btn" aria-haspopup="true" '
            f'aria-expanded="false">{esc(glabel)}</button>'
            f'<div class="nav-dropdown">{"".join(parts)}</div></div>'
        )

    # top-level order: 首页 | 读书笔记▾ | 实战方案▾ | 产品规划 | 知识库 | 站点▾
    items = [link("index.html", "首页", "index")]
    items.append(group_html(*groups[0]))
    items.append(group_html(*groups[1]))
    items.append(link("product.html", "产品规划", "product"))
    # /kb/ 由宿主机 nginx 反代到 kb-nativo workbench 容器，不在 dist 内，故为绝对路径
    items.append('<a href="/kb/">知识库</a>')
    items.append(group_html(*groups[2]))
    items = "".join(items)
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
    out.append(f'<a href="{base}sitemap.html" data-search="导览 站点地图 指南 路径 板块 新手">站点地图</a>')
    out.append(f'<a href="{base}concepts/index.html" data-search="概念 索引 词条">概念索引（{len(CONCEPTS)}）</a>')
    out.append(f'<a href="{base}pilot.html" data-search="试点 品牌 跨境电商 操作序列 案例">从书到试点</a>')
    out.append(f'<a href="{base}pilot-assets.html" data-search="资产 场景 规格 skill 契约 试点">试点资产地图</a>')
    out.append(f'<a href="{base}brand-plan.html" data-search="实战 路线图 阶段 门禁 波次 品牌域">品牌域实战路线图</a>')
    out.append(f'<a href="{base}orgmap.html" data-search="组织 岗位 价值流 场景 平面 绑定 一张图">组织与价值流一张图</a>')
    out.append(f'<a href="{base}product.html" data-search="产品 sage 出海 数字员工 场景 工具 四档">Sage 产品层规划</a>')
    out.append(f'<a href="{base}tools/index.html" data-search="工具 附录 清单">随书工具（{len(TOOLS)}）</a>')
    out.append(f'<a href="{base}terms.html" data-search="术语 术语表 代号 决策">方案术语表</a>')
    out.append(f'<a href="{base}about.html" data-search="关于 版权 引用">关于与引用规范</a>')
    out.append('</div><p class="dir-empty" hidden>没有匹配的目录项。</p></aside>')
    return "".join(out)


def sidebar_html_b2(base: str, current_slug: str = "") -> str:
    """Left directory for book 2 pages: two parts, deep reads linked, rest to map."""
    part_names = {"renzhi": "第一部分 · 数字时代品牌新认知（1–11）",
                  "xingdong": "第二部分 · 数字时代品牌增长新行动（12–25）"}
    out = ['<aside class="dir" aria-label="品牌书目录">',
           '<div class="dir-search"><label for="dir-search">搜索目录</label>',
           '<input id="dir-search" type="search" placeholder="章节、概念…" autocomplete="off"></div>']
    for part in BOOK2["parts"]:
        out.append(f'<div class="dir-group"><h4>{escape(part_names[part["key"]])}</h4>')
        for c in BOOK2["chapters"]:
            if c["part"] != part["key"]:
                continue
            deep = c.get("deep")
            if deep and deep in BRAND2_CONTENT:
                href = f'{base}brand2/{deep}.html'
                cur = ' aria-current="page"' if deep == current_slug else ""
                hay = f'第{c["no"]}章 {c["title"]}'
                out.append(f'<a href="{href}"{cur} data-search="{escape(hay, quote=True)}">'
                           f'<span class="no">{c["no"]}</span>{escape(c["title"])}'
                           f'<span class="soon" style="border-color:var(--r-blue);color:var(--r-blue)">精读</span></a>')
            else:
                href = f'{base}brand2/index.html#ch-{c["no"]}'
                hay = f'第{c["no"]}章 {c["title"]}'
                out.append(f'<a href="{href}" data-search="{escape(hay, quote=True)}">'
                           f'<span class="no">{c["no"]}</span>{escape(c["title"])}</a>')
        out.append('</div>')
    out.append('<div class="dir-group"><h4>整合</h4>')
    out.append(f'<a href="{base}synthesis.html" data-search="两书合璧 整合 品牌 增长">两书合璧 · 整合页</a>')
    out.append(f'<a href="{base}index.html" data-search="第一本书 AI Native 组织">← 返回第一本书</a>')
    out.append('</div><p class="dir-empty" hidden>没有匹配的目录项。</p></aside>')
    return "".join(out)


def sidebar_html_b3(base: str, current_slug: str = "") -> str:
    """Left directory for book 3 pages: four parts, deep reads linked, rest to map."""
    part_names = {p["key"]: p["name"] for p in BOOK3["parts"]}
    out = ['<aside class="dir" aria-label="本体书目录">',
           '<div class="dir-search"><label for="dir-search">搜索目录</label>',
           '<input id="dir-search" type="search" placeholder="章节、概念…" autocomplete="off"></div>']
    for part in BOOK3["parts"]:
        out.append(f'<div class="dir-group"><h4>{escape(part_names[part["key"]])}</h4>')
        for c in BOOK3["chapters"]:
            if c["part"] != part["key"]:
                continue
            deep = c.get("deep")
            hay = f'第{c["no"]}章 {c["title"]}'
            if deep and deep in BOOK3_CONTENT:
                href = f'{base}book3/{deep}.html'
                cur = ' aria-current="page"' if deep == current_slug else ""
                out.append(f'<a href="{href}"{cur} data-search="{escape(hay, quote=True)}">'
                           f'<span class="no">{c["no"]}</span>{escape(c["title"])}'
                           f'<span class="soon" style="border-color:var(--r-blue);color:var(--r-blue)">精读</span></a>')
            else:
                href = f'{base}book3/index.html#ch-{c["no"]}'
                out.append(f'<a href="{href}" data-search="{escape(hay, quote=True)}">'
                           f'<span class="no">{c["no"]}</span>{escape(c["title"])}</a>')
        out.append('</div>')
    out.append('<div class="dir-group"><h4>关联</h4>')
    out.append(f'<a href="{base}semantic.html" data-search="语义底座 术语 对象 权限">语义底座 v0 · 本书方法落地页</a>')
    out.append(f'<a href="{base}index.html" data-search="返回首页">← 返回首页</a>')
    out.append('</div><p class="dir-empty" hidden>没有匹配的目录项。</p></aside>')
    return "".join(out)


def sidebar_html_b4(base: str, current_slug: str = "") -> str:
    """Left directory for book 4 pages: three parts, deep reads linked, rest to map."""
    part_names = {p["key"]: p["name"] for p in BOOK4["parts"]}
    out = ['<aside class="dir" aria-label="Agent书目录">',
           '<div class="dir-search"><label for="dir-search">搜索目录</label>',
           '<input id="dir-search" type="search" placeholder="章节、概念…" autocomplete="off"></div>']
    for part in BOOK4["parts"]:
        out.append(f'<div class="dir-group"><h4>{escape(part_names[part["key"]])}</h4>')
        for c in BOOK4["chapters"]:
            if c["part"] != part["key"]:
                continue
            deep = c.get("deep")
            hay = f'第{c["no"]}章 {c["title"]}'
            if deep and deep in BOOK4_CONTENT:
                href = f'{base}book4/{deep}.html'
                cur = ' aria-current="page"' if deep == current_slug else ""
                out.append(f'<a href="{href}"{cur} data-search="{escape(hay, quote=True)}">'
                           f'<span class="no">{c["no"]}</span>{escape(c["title"])}'
                           f'<span class="soon" style="border-color:var(--r-blue);color:var(--r-blue)">精读</span></a>')
            else:
                href = f'{base}book4/index.html#ch-{c["no"]}'
                out.append(f'<a href="{href}" data-search="{escape(hay, quote=True)}">'
                           f'<span class="no">{c["no"]}</span>{escape(c["title"])}</a>')
        out.append('</div>')
    out.append('<div class="dir-group"><h4>关联</h4>')
    out.append(f'<a href="{base}agent-lab.html" data-search="映射 toyagent 实验场 三方">Agent 实验场 · 三方映射</a>')
    out.append(f'<a href="{base}experiments.html" data-search="实验 配套 代码 skill 复现">配套实验 · 110 实验 + 22 Skill</a>')
    out.append(f'<a href="{base}toyagent-steps.html" data-search="toyagent 原理文章 蒸馏 机制">原理文章蒸馏 · 27 篇机制提炼</a>')
    out.append(f'<a href="{base}stack.html" data-search="四层架构 组织 业务 语义 工程">四层架构 · 0→1 路径</a>')
    out.append(f'<a href="{base}index.html" data-search="返回首页">← 返回首页</a>')
    out.append('</div><p class="dir-empty" hidden>没有匹配的目录项。</p></aside>')
    return "".join(out)


def sidebar_html_pb(base: str, current_slug: str = "") -> str:
    """Left directory for agent-playbook pages: build-path nodes + expansion nodes."""
    out = ['<aside class="dir" aria-label="Agent Playbook 目录">',
           '<div class="dir-search"><label for="dir-search">搜索目录</label>',
           '<input id="dir-search" type="search" placeholder="节点、章节、概念…" autocomplete="off"></div>']
    out.append('<div class="dir-group"><h4>框架</h4>')
    out.append(f'<a href="{base}agent-playbook/index.html" data-search="框架 P0-P8 路线图 模型边界 autoagent">0→1 框架总纲 · 模型边界矩阵</a>')
    out.append('</div>')
    out.append('<div class="dir-group"><h4>构建路径 · 必建节点</h4>')
    for n in AGENT_PLAYBOOK.get("nodes", []):
        if not str(n.get("tier", "")).startswith("必建"):
            continue
        hay = f'{n["no"]} {n["title"]}'
        if n.get("status") == "published":
            href = f'{base}agent-playbook/{n["slug"]}.html'
            cur = ' aria-current="page"' if n["slug"] == current_slug else ""
            out.append(f'<a href="{href}"{cur} data-search="{escape(hay, quote=True)}">'
                       f'<span class="no">{n["no"]}</span>{escape(n["title"])}'
                       f'<span class="soon" style="border-color:var(--r-blue);color:var(--r-blue)">节点</span></a>')
        else:
            href = n.get("source_url") or f'{base}agent-playbook/index.html'
            out.append(f'<a href="{href}" data-search="{escape(hay, quote=True)}" target="_blank" rel="noopener">'
                       f'<span class="no">{n["no"]}</span>{escape(n["title"])}'
                       f'<span class="soon">规划中</span></a>')
    out.append('</div>')
    out.append('<div class="dir-group"><h4>扩展形态 · 按需选装</h4>')
    for n in AGENT_PLAYBOOK.get("nodes", []):
        if str(n.get("tier", "")).startswith("必建"):
            continue
        hay = f'{n["no"]} {n["title"]}'
        if n.get("status") == "published":
            href = f'{base}agent-playbook/{n["slug"]}.html'
            cur = ' aria-current="page"' if n["slug"] == current_slug else ""
            out.append(f'<a href="{href}"{cur} data-search="{escape(hay, quote=True)}">'
                       f'<span class="no">{n["no"]}</span>{escape(n["title"])}'
                       f'<span class="soon" style="border-color:var(--r-blue);color:var(--r-blue)">{escape(n.get("tier", ""))}</span></a>')
        else:
            href = n.get("source_url") or f'{base}agent-playbook/index.html'
            out.append(f'<a href="{href}" data-search="{escape(hay, quote=True)}" target="_blank" rel="noopener">'
                       f'<span class="no">{n["no"]}</span>{escape(n["title"])}'
                       f'<span class="soon">{escape(n.get("tier", ""))}</span></a>')
    out.append('</div>')
    out.append('<div class="dir-group"><h4>关联</h4>')
    out.append(f'<a href="{base}book4/index.html" data-search="书4 agent 深入理解 精读">Agent书 · 深入理解 AI Agent</a>')
    out.append(f'<a href="{base}agent-lab.html" data-search="映射 toyagent 实验场 三方">Agent 实验场 · 三方映射</a>')
    out.append(f'<a href="{base}toyagent-steps.html" data-search="toyagent 原理文章 蒸馏">原理文章蒸馏 · 27 篇</a>')
    out.append(f'<a href="{base}stack.html" data-search="四层架构 组织 业务 语义 工程">四层架构 · 0→1 路径</a>')
    out.append(f'<a href="{base}experiments.html" data-search="实验 配套 代码 skill">配套实验 · 110 实验</a>')
    out.append(f'<a href="{base}index.html" data-search="返回首页">← 返回首页</a>')
    out.append('</div><p class="dir-empty" hidden>没有匹配的目录项。</p></aside>')
    return "".join(out)


def sidebar_html_af(base: str, current_slug: str = "") -> str:
    """Left directory for agent-field pages: framework + field pages."""
    out = ['<aside class="dir" aria-label="Agent Field Guide 目录">',
           '<div class="dir-search"><label for="dir-search">搜索目录</label>',
           '<input id="dir-search" type="search" placeholder="页面、主题、概念…" autocomplete="off"></div>']
    out.append('<div class="dir-group"><h4>框架</h4>')
    out.append(f'<a href="{base}agent-field/index.html" data-search="框架 第二参照系 边界 mas_router">0→1 工程实录 · 框架总纲</a>')
    out.append('</div>')
    out.append('<div class="dir-group"><h4>方法论页面</h4>')
    for p in AGENT_FIELD.get("pages", []):
        if p.get("slug") == "index":
            continue
        hay = f'{p.get("no", "")} {p["title"]}'
        cur = ' aria-current="page"' if p.get("slug") == current_slug else ""
        if p.get("status") == "published":
            href = f'{base}agent-field/{p["slug"]}.html'
            out.append(f'<a href="{href}"{cur} data-search="{escape(hay, quote=True)}">'
                       f'<span class="no">{p.get("no", "")}</span>{escape(p["title"])}'
                       f'<span class="soon" style="border-color:var(--r-blue);color:var(--r-blue)">实录</span></a>')
        else:
            out.append(f'<a href="{base}agent-field/index.html" data-search="{escape(hay, quote=True)}">'
                       f'<span class="no">{p.get("no", "")}</span>{escape(p["title"])}'
                       f'<span class="soon">规划中</span></a>')
    out.append('</div>')
    out.append('<div class="dir-group"><h4>关联</h4>')
    out.append(f'<a href="{base}agent-playbook/index.html" data-search="playbook P0-P8 构建脊柱">Agent Playbook · 0→1 构建脊柱</a>')
    out.append(f'<a href="{base}agent-lab.html" data-search="映射 toyagent 实验场">Agent 实验场 · 三方映射</a>')
    out.append(f'<a href="{AGENT_FIELD.get("source_url", "https://github.com/zjgulai/mas_router_method")}" data-search="mas_router_method 源码仓库" target="_blank" rel="noopener">mas_router_method 仓库 ↗</a>')
    out.append(f'<a href="{base}index.html" data-search="返回首页">← 返回首页</a>')
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
<div class="col"><h4>导航</h4><p><a href="{base}index.html">全书地图</a><br><a href="{base}sitemap.html">站点地图</a><br><a href="{base}chapters/index.html">章节解读</a><br><a href="{base}concepts/index.html">概念索引</a><br><a href="{base}brand2/index.html">品牌书·弱品牌强品牌</a><br><a href="{base}book3/index.html">本体书·本体驱动AI数据管理</a><br><a href="{base}book4/index.html">Agent书·深入理解AI Agent</a><br><a href="{base}agent-lab.html">Agent实验场</a><br><a href="{base}experiments.html">配套实验</a><br><a href="{base}toyagent-steps.html">原理文章蒸馏</a><br><a href="{base}agent-playbook/index.html">Agent Playbook·0到1</a><br><a href="{base}agent-field/index.html">Agent Field Guide·工程实录</a><br><a href="{base}triology.html">三书合璧</a><br><a href="{base}synthesis.html">两书合璧</a><br><a href="{base}stack.html">四层架构</a><br><a href="{base}semantic.html">语义底座 v0</a><br><a href="{base}pilot.html">从书到试点</a><br><a href="{base}pilot-assets.html">试点资产地图</a><br><a href="{base}brand-plan.html">品牌域实战路线图</a><br><a href="{base}orgmap.html">组织与价值流一张图</a><br><a href="{base}product.html">Sage 产品层规划</a><br><a href="{base}tools/index.html">随书工具</a><br><a href="{base}terms.html">方案术语表</a><br><a href="{base}about.html">关于</a></p></div>
<div class="col"><h4>原书</h4><p>{escape(BOOK['title'])}<br>{escape(BOOK['author'])} 著 · {escape(BOOK['publisher'])} · {escape(BOOK['isbn'])}<br><br>{escape(BOOK2['title'])}<br>{escape(BOOK2['author'])} 著 · {escape(BOOK2['publisher'])} · {escape(BOOK2['isbn'])}<br><br>{escape(BOOK3['title'])}<br>{escape(BOOK3['author'])} 著 · {escape(BOOK3['publisher'])} · {escape(BOOK3['isbn'])}<br><br>{escape(BOOK4['title'])}<br>{escape(BOOK4['author'])} 著 · {escape(BOOK4['publisher'])} · <a href="{BOOK4['repo']}" style="color:inherit">GitHub ↗</a><br><br>《AI Agent 通识教程》30 章<br>小傅哥 · <a href="https://ai-agent-guide.xiaofuge.cn/" style="color:inherit">ai-agent-guide.xiaofuge.cn ↗</a></p></div>
</div><div class="wrap legal">本站内容为读书笔记性质的 transformative use；图像裁自原书 PDF 供个人精读参考。引用规范见<a href="{base}about.html">关于页</a>。</div></footer>
<script src="{base}assets/site.js" defer></script>
</body></html>"""


def reader_page(base: str, current_slug: str, article_inner: str,
                headings: list, title: str, desc: str,
                nav_current: str = "chapters", sidebar: str | None = None) -> str:
    body = (
        '<main class="reader">'
        '<button class="menu-toggle mobile-dir-btn" aria-expanded="false">目录</button>'
        + (sidebar if sidebar is not None else sidebar_html(base, current_slug))
        + f'<article class="article" id="article">{article_inner}</article>'
        + ptoc_html(headings)
        + '</main>'
    )
    return page_shell(title, base, nav_current, body, desc)
