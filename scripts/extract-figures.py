#!/usr/bin/env python3
"""Extract vector figures from the book PDF into WebP crops.

The book PDF contains no raster images; all 54 figures are vector path art
mixed with text on the same pages. This script:

1. Runs `pdftotext -bbox` to locate each figure caption ("图 X-Y").
2. Runs `pdftocairo -svg` and walks the SVG, accumulating transform
   matrices, to collect page-space bounding boxes of every drawing element
   (paths, rects, lines, images) and every text-glyph anchor (<use>).
3. Clusters drawing elements into figure candidates, assigns each caption
   to the nearest cluster, expands the box to swallow enclosed text labels,
   and renders the region with `pdftoppm` + `cwebp`.

Usage:
    python3 scripts/extract-figures.py --pdf "path/to/book.pdf" \
        --manifest assets/figures/figures.json --out assets/figures
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}"

# cluster gap (pt) and padding (pt) tuned for 880x1230pt book pages
CLUSTER_GAP = 14.0
PAD = 10.0
LABEL_MARGIN = 6.0

# SVG subtrees that never render visible geometry on the page itself
SKIP_TAGS = {"defs", "clipPath", "mask", "filter", "title", "desc",
             "metadata", "style", "symbol"}


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{proc.stderr}")


def page_size(pdf: Path, page_no: int) -> tuple[float, float]:
    """Page size in pt via pdfinfo is overkill; read from SVG instead."""
    raise NotImplementedError


# ---------------------------------------------------------------- SVG parse


def parse_transform(value: str | None) -> tuple[float, float, float, float, float, float]:
    """Return matrix (a,b,c,d,e,f); identity when absent."""
    if not value:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    m = re.match(r"matrix\(([^)]+)\)", value.strip())
    if m:
        a, b, c, d, e, f = (float(v) for v in re.split(r"[\s,]+", m.group(1).strip()) if v)
        return (a, b, c, d, e, f)
    m = re.match(r"translate\(([^)]+)\)", value.strip())
    if m:
        parts = [float(v) for v in re.split(r"[\s,]+", m.group(1).strip()) if v]
        return (1.0, 0.0, 0.0, 1.0, parts[0], parts[1] if len(parts) > 1 else 0.0)
    m = re.match(r"scale\(([^)]+)\)", value.strip())
    if m:
        parts = [float(v) for v in re.split(r"[\s,]+", m.group(1).strip()) if v]
        sx = parts[0]
        sy = parts[1] if len(parts) > 1 else sx
        return (sx, 0.0, 0.0, sy, 0.0, 0.0)
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mat_mul(m1, m2):
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def mat_pt(m, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def path_points(d: str) -> list[tuple[float, float]]:
    """Extract (x, y) coordinate pairs from an SVG path `d` attribute."""
    tokens = re.findall(r"[A-Za-z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d)
    pts: list[tuple[float, float]] = []
    i = 0
    cur_cmd = ""
    nums: list[float] = []

    def flush() -> None:
        nonlocal nums
        # pair up numbers; odd trailing number is a flag (e.g. arc rotation)
        for j in range(0, len(nums) - 1, 2):
            pts.append((nums[j], nums[j + 1]))
        nums = []

    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha():
            if cur_cmd and nums:
                flush()
            cur_cmd = tok
            i += 1
            continue
        nums.append(float(tok))
        i += 1
        # Heuristic arity per command for implicit repetition handling.
        arity = {
            "M": 2, "L": 2, "T": 2, "H": 1, "V": 1,
            "C": 6, "S": 4, "Q": 4, "A": 7, "Z": 0,
        }.get(cur_cmd.upper(), 2)
        if cur_cmd.upper() == "Z":
            flush()
            cur_cmd = ""
            continue
        if len(nums) >= arity and arity > 0:
            flush()
    flush()
    return pts


def bbox_of_points(pts: list[tuple[float, float]]) -> tuple[float, float, float, float] | None:
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def transform_bbox(m, bb) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = bb
    corners = [mat_pt(m, x, y) for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return (min(xs), min(ys), max(xs), max(ys))


def collect_page_elements(svg_path: Path) -> tuple[list, list, tuple[float, float]]:
    """Return (art_boxes, label_points, page_size_pt)."""
    tree = ET.parse(svg_path)
    root = tree.getroot()
    page_w = float(root.get("width", "0").replace("pt", ""))
    page_h = float(root.get("height", "0").replace("pt", ""))

    # Index every id'd element so non-glyph <use> references (figure symbols
    # such as <g id="source-N">) can be resolved back to their geometry.
    id_map = {}
    for el in root.iter():
        eid = el.get("id")
        if eid:
            id_map[eid] = el

    art: list[tuple[float, float, float, float]] = []   # vector drawing boxes (pt)
    labels: list[tuple[float, float]] = []               # text-glyph anchor points (pt)

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    XLINK_HREF = "{http://www.w3.org/1999/xlink}href"

    def handle(el, matrix, depth=0):
        tag = local(el.tag)
        if tag in SKIP_TAGS:
            return
        m = mat_mul(matrix, parse_transform(el.get("transform")))
        if tag == "path":
            pts = path_points(el.get("d", ""))
            bb = bbox_of_points(pts)
            if bb:
                art.append(transform_bbox(m, bb))
        elif tag in ("rect", "line", "polyline", "polygon", "circle", "ellipse"):
            bb = shape_bbox(el)
            if bb:
                art.append(transform_bbox(m, bb))
        elif tag == "image":
            try:
                x = float(el.get("x", 0)); y = float(el.get("y", 0))
                w = float(el.get("width", 0)); h = float(el.get("height", 0))
                art.append(transform_bbox(m, (x, y, x + w, y + h)))
            except ValueError:
                pass
        elif tag == "use":
            href = el.get(XLINK_HREF) or el.get("href") or ""
            ref_id = href.lstrip("#")
            if ref_id.startswith("glyph"):
                try:
                    x = float(el.get("x", 0) or 0)
                    y = float(el.get("y", 0) or 0)
                    px, py = mat_pt(m, x, y)
                    labels.append((px, py))
                except ValueError:
                    pass
            elif depth < 4 and ref_id in id_map:
                # Figure symbol: x/y act as a translate appended after the
                # element's own transform list (applied to content first).
                try:
                    ux = float(el.get("x", 0) or 0)
                    uy = float(el.get("y", 0) or 0)
                except ValueError:
                    ux = uy = 0.0
                content_m = mat_mul(m, (1.0, 0.0, 0.0, 1.0, ux, uy))
                handle(id_map[ref_id], content_m, depth + 1)
        for child in el:
            handle(child, m, depth)

    handle(root, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    return art, labels, (page_w, page_h)


def shape_bbox(el) -> tuple[float, float, float, float] | None:
    tag = local(el.tag)
    try:
        if tag == "rect":
            x = float(el.get("x", 0)); y = float(el.get("y", 0))
            w = float(el.get("width", 0)); h = float(el.get("height", 0))
            return (x, y, x + w, y + h)
        if tag == "line":
            x1 = float(el.get("x1", 0)); y1 = float(el.get("y1", 0))
            x2 = float(el.get("x2", 0)); y2 = float(el.get("y2", 0))
            return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        if tag in ("polyline", "polygon"):
            nums = [float(v) for v in re.findall(r"[-+]?\d+\.?\d*", el.get("points", ""))]
            if len(nums) >= 4:
                xs, ys = nums[0::2], nums[1::2]
                return (min(xs), min(ys), max(xs), max(ys))
        if tag in ("circle", "ellipse"):
            cx = float(el.get("cx", 0)); cy = float(el.get("cy", 0))
            rx = float(el.get("r", el.get("rx", 0)) or 0)
            ry = float(el.get("r", el.get("ry", 0)) or 0)
            return (cx - rx, cy - ry, cx + rx, cy + ry)
    except (ValueError, TypeError):
        return None
    return None


# ------------------------------------------------------- clustering & assign


def cluster_boxes(boxes: list, gap: float) -> list[list]:
    """Greedy proximity clustering of (x0,y0,x1,y1) boxes."""
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    clusters: list[list] = []
    for bb in boxes:
        placed = False
        for cl in clusters:
            cx0 = min(b[0] for b in cl); cy0 = min(b[1] for b in cl)
            cx1 = max(b[2] for b in cl); cy1 = max(b[3] for b in cl)
            # merge if box intersects expanded cluster bbox
            if not (bb[0] > cx1 + gap or bb[2] < cx0 - gap or
                    bb[1] > cy1 + gap or bb[3] < cy0 - gap):
                cl.append(bb)
                placed = True
                break
        if not placed:
            clusters.append([bb])
    # merge pass: clusters may need re-merge after growth (single pass is
    # usually enough for page layouts; do a second conservative pass)
    merged = True
    while merged:
        merged = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                a, b = clusters[i], clusters[j]
                ax0 = min(x[0] for x in a); ay0 = min(x[1] for x in a)
                ax1 = max(x[2] for x in a); ay1 = max(x[3] for x in a)
                bx0 = min(x[0] for x in b); by0 = min(x[1] for x in b)
                bx1 = max(x[2] for x in b); by1 = max(x[3] for x in b)
                if not (bx0 > ax1 + gap or bx1 < ax0 - gap or
                        by0 > ay1 + gap or by1 < ay0 - gap):
                    clusters[i] = a + b
                    del clusters[j]
                    merged = True
                    break
            if merged:
                break
    return clusters


def union_box(boxes: list) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes), min(b[1] for b in boxes),
        max(b[2] for b in boxes), max(b[3] for b in boxes),
    )


def cluster_area(cl) -> float:
    x0, y0, x1, y1 = union_box(cl)
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def caption_positions(pdf: Path, page_no: int) -> list[tuple[float, float, str]]:
    """Return (cx, cy, text) for caption-like words via pdftotext -bbox."""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "bbox.html"
        run(["pdftotext", "-f", str(page_no), "-l", str(page_no),
             "-bbox", str(pdf), str(out)])
        tree = ET.parse(out)
    root = tree.getroot()
    words = []
    for w in root.iter():
        if local(w.tag) != "word":
            continue
        text = "".join(w.itertext()).strip()
        if not text:
            continue
        try:
            x0 = float(w.get("xMin", 0)); y0 = float(w.get("yMin", 0))
            x1 = float(w.get("xMax", 0)); y1 = float(w.get("yMax", 0))
        except ValueError:
            continue
        words.append(((x0 + x1) / 2, (y0 + y1) / 2, text))
    return words


def find_caption_y(words: list, fig_id: str) -> float | None:
    """Find y-center of caption '图 X-Y' on the page."""
    chap, num = fig_id.removeprefix("fig-").split("-")
    target_num = num
    # caption renders as '图' + '5-4' (two words) or single '图5-4'
    for i, (cx, cy, text) in enumerate(words):
        if text == "图" and i + 1 < len(words):
            nxt = words[i + 1][2]
            if nxt == f"{chap}-{target_num}":
                return cy
        if re.fullmatch(rf"图\s*{chap}-{target_num}", text):
            return cy
    return None


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


# ------------------------------------------------------------------- render


def extract_figure(pdf: Path, page_no: int, fig_id: str,
                   dpi: int = 200) -> tuple[bytes | None, dict]:
    """Render one figure; returns (png_bytes_or_None, info_dict)."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # single-page -svg writes exactly the prefix path (no extension added)
        svg_out = td / f"p{page_no}"
        run(["pdftocairo", "-f", str(page_no), "-l", str(page_no),
             "-svg", str(pdf), str(svg_out)])
        actual = svg_out if svg_out.exists() else next(td.glob("p*"), None)
        if actual is None or not actual.exists():
            return None, {"error": "no svg produced"}
        art, labels, (pw, ph) = collect_page_elements(actual)

        words = caption_positions(pdf, page_no)
        cap_y = find_caption_y(words, fig_id)

        clusters = cluster_boxes(art, CLUSTER_GAP) if art else []
        if not clusters:
            return None, {"art_boxes": 0, "note": "no vector art on page"}

        # candidate figure clusters: area above a threshold fraction of page
        page_area = pw * ph
        big = [c for c in clusters if cluster_area(c) > page_area * 0.01]
        pool = big if big else clusters

        if cap_y is not None and len(pool) > 1:
            # choose cluster whose vertical span is nearest the caption;
            # interval distance (not center distance) so stacked figures on
            # one page each pick their own cluster
            def cdist(cl):
                _, cy0, _, cy1 = union_box(cl)
                if cap_y < cy0:
                    return cy0 - cap_y
                if cap_y > cy1:
                    return cap_y - cy1
                return 0.0
            chosen = min(pool, key=cdist)
        else:
            chosen = max(pool, key=cluster_area)

        x0, y0, x1, y1 = union_box(chosen)
        # expand to include text labels whose anchor sits inside padded box
        ex0, ey0, ex1, ey1 = x0 - PAD, y0 - PAD, x1 + PAD, y1 + PAD
        # when the "图 X-Y" caption marker sits at/below the art cluster, the
        # caption block (marker + descriptive line) must not be swallowed
        cap_below = cap_y is not None and cap_y > y1 - PAD
        for (lx, ly) in labels:
            if cap_below and ly > cap_y - 8:
                continue
            if ex0 - LABEL_MARGIN <= lx <= ex1 + LABEL_MARGIN and \
               ey0 - LABEL_MARGIN <= ly <= ey1 + LABEL_MARGIN:
                ex0, ey0 = min(ex0, lx - 12), min(ey0, ly - 12)
                ex1, ey1 = max(ex1, lx + 12), max(ey1, ly + 12)
        if cap_below:
            ey1 = min(ey1, cap_y - 6)
        # clamp to page
        ex0, ey0 = max(0, ex0), max(0, ey0)
        ex1, ey1 = min(pw, ex1), min(ph, ey1)

        scale = dpi / 72.0
        px = int(ex0 * scale); py = int(ey0 * scale)
        pw_px = max(1, int((ex1 - ex0) * scale))
        ph_px = max(1, int((ey1 - ey0) * scale))

        png = td / f"{fig_id}.png"
        run(["pdftoppm", "-f", str(page_no), "-l", str(page_no),
             "-r", str(dpi), "-png", "-x", str(px), "-y", str(py),
             "-W", str(pw_px), "-H", str(ph_px),
             str(pdf), str(td / "crop")])
        del png  # bytes returned below; path unused
        produced = list(td.glob("crop*.png"))
        if not produced:
            return None, {"error": "pdftoppm produced nothing"}
        png_bytes = produced[0].read_bytes()

        info = {
            "page": page_no,
            "pdf_box_pt": [round(v, 1) for v in (ex0, ey0, ex1, ey1)],
            "clusters": len(clusters),
            "chosen_cluster": len(chosen),
            "caption_y": cap_y,
        }
        return png_bytes, info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path,
                    help="JSON: {\"fig-5-1\": {\"page\": 82, \"chapter\": 5, \"num\": 1, \"caption\": \"...\"}}")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    results = {}
    tmp_pngs: dict[str, Path] = {}

    # Phase 1: locate + render all crops into temp files
    with tempfile.TemporaryDirectory() as td:
        for fig_id, meta in manifest.items():
            if args.only and fig_id not in args.only:
                continue
            page_no = int(meta["page"])
            print(f"[{fig_id}] page {page_no} ...", flush=True)
            png, info = extract_figure(args.pdf, page_no, fig_id, args.dpi)
            if png is None:
                results[fig_id] = {**meta, "status": "failed", **info}
                print(f"  -> FAILED: {info}")
                continue
            # copy into a stable temp location keyed by fig id
            dest = Path(td) / f"{fig_id}.png"
            dest.write_bytes(png)
            tmp_pngs[fig_id] = dest
            results[fig_id] = {**meta, "status": "ok", **info}
            print(f"  -> box {info.get('pdf_box_pt')} ({info.get('chosen_cluster')} elems)")

        # Phase 2: convert to webp
        for fig_id, png in tmp_pngs.items():
            webp = args.out / f"{fig_id}.webp"
            run(["cwebp", "-q", "88", str(png), "-o", str(webp)])
            results[fig_id]["file"] = webp.name
            results[fig_id]["bytes"] = webp.stat().st_size

    (args.out / "manifest.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results.values() if r.get("status") == "ok")
    print(f"\nDone: {ok}/{len(results)} figures extracted -> {args.out}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
