# Native AI Organ · 读书站

《AI Native 组织：从思考到实践》（吕承通 著，电子工业出版社）深度解读笔记站。
个人精读库：章节原创蒸馏 + 书中插图 + 短引用（标注页码）+ 概念索引 + 随书工具清单。

## 内容结构

- `src/data/book.json` — 书籍元信息
- `src/data/chapters-index.json` — 全书 16 个阅读单元（序章 + 13 章 + 终章）与「道—术—器」分篇
- `src/data/chapters/*.json` — 已发布章节的解读正文（block JSON，含实践映射）
- `src/data/concepts.json` — 概念索引词条
- `src/data/tools.json` — 附录 A 工具 + 转型日历（可勾选清单）
- `assets/figures/` — 从原书 PDF 矢量裁剪的 WebP 插图 + `figures.json`（图号/页码/图注清单）+ `manifest.json`（导出状态）

## 构建

纯 Python 标准库，无依赖：

```bash
python3 build.py          # 生成 dist/
python3 build.py --check  # 构建并校验内部链接与图片引用
```

本地预览：

```bash
cd dist && python3 -m http.server 8000
```

## 插图再生成（可选）

`assets/figures/figures.json` 已含全部 54 幅图的图号/页码/图注。
重新导出需要 PyMuPDF + poppler（`pdftotext`/`pdftocairo`/`pdftoppm`）+ `cwebp`：

```bash
uv venv /tmp/bookimg/.venv && /tmp/bookimg/.venv/bin/pip install pymupdf
/tmp/bookimg/.venv/bin/python scripts/extract-figures.py \
  --pdf "/path/to/AI Native组织.pdf" \
  --manifest assets/figures/figures.json --out assets/figures
```

## 版权

解读内容为原创蒸馏；短引用单处 ≤80 字并标注原书页码；插图裁自原书 PDF 仅供个人精读参考。
详见站内「关于」页。原书 PDF 不进本仓库。
