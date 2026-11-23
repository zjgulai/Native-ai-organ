"""Page-level renderers: home, chapter, chapters index, concepts, tools, about."""
import re
from html import escape

from site_data import (BOOK, CHAPTERS, CHAPTER_CONTENT, CONCEPTS, TOOLS,
                       TERMS, PILOT, FIG_SRC, SITE_NAME)
from site_render import (inline, render_blocks, page_shell, reader_page)


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
    hero = f"""
<section class="hero"><div class="wrap">
<div>
<p class="eyebrow">深度解读 · Reading Notes</p>
<h1>{escape(BOOK['title'])}<br><em>从思考到实践</em></h1>
<p class="lead">{escape(BOOK.get('thesis', ''))}</p>
<div class="meta">
<div><b>{BOOK.get('pages', '271')}</b>页原书</div>
<div><b>{len(CHAPTERS)}</b>章正文</div>
<div><b>{len(CONCEPTS)}</b>概念词条</div>
<div><b>{len(TOOLS)}</b>随书工具</div>
<div><b>{len(FIG_SRC)}</b>幅原书插图</div>
</div></div>
<div class="book-card"><div class="kicker">THE BOOK</div>
<h2>{escape(BOOK['title'])}</h2>
<div class="author">{escape(BOOK['author'])} 著 · {escape(BOOK['publisher'])} · {escape(BOOK['isbn'])} · {escape(BOOK.get('pub_date', '2026.10'))}</div>
<div class="thesis"><q>本书聚焦于人工智能时代组织管理的根本变化——当 AI 从"人使用的工具"进化为"能够独立做事的主体"时，企业的知识、权力、协作与组织结构应如何重新设计。</q><br>—— 内容简介</div></div>
</div></section>"""
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
    body = hero + f"""
<section class="section"><div class="wrap">
<h2>全书地图</h2>
<p class="sec-sub">以「道—术—器」为主线：先理解原理，再建立方法，最后落地工程。每篇解读保留原书论证线，并附实践映射。</p>
<div class="map-grid">{''.join(cards)}</div></div></section>
<section class="section tint"><div class="wrap">
<h2>方法链：这本书为什么要按这个顺序读</h2>
<p class="sec-sub">每一层都以相邻层为前提：道回答「为什么」，术回答「怎么分工」，器回答「靠什么运行」，路线图回答「先做什么」，行业与个人回答「落到谁身上」。跳层阅读会得到结论，顺序阅读才能得到方法。</p>
{chain_html}
<h3 style="margin:34px 0 6px">三条推荐阅读路径</h3>
{path_html}</div></section>
<section class="section"><div class="wrap">
<div class="cta-card">
<div><span class="idx">BRIDGE</span><h3>从书到试点：品牌域试点操作序列</h3>
<p>读完全书之后第一步做什么——价值链断点地图、首个 Case 模板、授权八问实例、十二道门、90 天节奏与 KPI 口径，全部写成可对照的操作清单。本站原创，非原书内容，不构成任何业务授权。</p></div>
<a class="go" href="{base}pilot.html">打开试点指南 →</a></div>
<p style="margin-top:14px;font-size:13px;color:#8a97a8">配套：<a href="{base}terms.html" style="color:var(--r-blue)">方案术语表</a> 解码各篇实践映射中的内部代号（D-020~D-053、Policy Gate、ArtifactEnvelope 等）。</p></div></section>
<section class="section tint"><div class="wrap">
<h2>章节解读</h2>
<p class="sec-sub">已发布章节可直接阅读；其余章节正在蒸馏中。</p>
<div class="ch-list">{ch_rows}</div></div></section>
<section class="section"><div class="wrap">
<h2>概念索引</h2>
<p class="sec-sub">从全书抽取的核心概念，每个词条给出蒸馏定义、出处与关联。</p>
<div class="concept-grid">{concept_cards}</div>
<p style="margin-top:18px"><a href="{base}concepts/index.html" style="color:var(--r-blue);font-weight:600">查看全部 {len(CONCEPTS)} 个概念 →</a></p></div></section>
<section class="section tint"><div class="wrap">
<h2>随书工具</h2>
<p class="sec-sub">附录 A 的实操工具，改写为可勾选、可打印的清单页。</p>
<div class="tool-grid">{tool_cards}</div></div></section>"""
    return page_shell(BOOK["title"], base, "index", f"<main>{body}</main>", BOOK.get("thesis", "")[:120])


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
<h2 id="s-about-3">实践映射说明</h2>
<p>每篇解读末尾的「实践映射」将书中框架对照作者本人的 AI 组织变革设计项目（约 50 个 AI 岗位、八阶段协同、Policy Gate 授权体系），属于本站原创的二次创作，与原书作者无关。</p>
<h2 id="s-about-4">技术</h2>
<p>纯静态站：Python 标准库构建（<code>build.py</code>），无前端框架与构建依赖；内容为 JSON 数据，页面为构建期渲染的 HTML；交互（目录筛选、本页目录、工具勾选）为渐进增强，不影响无 JS 阅读。</p>"""
    return page_shell("关于本站", base, "about", inner, "关于本站与引用规范")
