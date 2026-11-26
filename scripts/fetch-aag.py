#!/usr/bin/env python3
"""Fetch ai-agent-guide.xiaofuge.cn chapter pages + write content fingerprint.

Downloads the 30 static chapter HTML files into scripts/.cache/aag/ and
records a per-chapter sha256 fingerprint at
src/data/agent-playbook/source-fingerprint.json for change detection.

Run:  python3 scripts/fetch-aag.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "scripts" / ".cache" / "aag"
FINGERPRINT = ROOT / "src" / "data" / "agent-playbook" / "source-fingerprint.json"
BASE = "https://ai-agent-guide.xiaofuge.cn/chapters/"

# chapters/ file names in pedagogical order (id order from site main.js)
CHAPTERS = [
    "ch00-fundamentals", "ch01-llm-basics", "ch02-what-is-agent",
    "ch03-weather-agent", "ch04-prompt-engineering",
    "ch04b-context-engineering", "ch04-react-pattern", "ch05-memory",
    "ch06-brain-intent-router", "ch21-loop-runtime-sandbox",
    "ch22-harness", "ch27-dsh-java-anatomy", "ch16-rag",
    "ch26-llm-wiki", "ch06-tools", "ch07-mcp", "ch08-skills",
    "ch09-cli-capability", "ch10-multi-agent", "ch11-langgraph",
    "ch12-framework-comparison", "ch13-dify-coze", "ch14-cli-agent",
    "ch15-gui-agent", "ch17-evaluation", "ch18-security",
    "ch19-deployment", "ch20-inference-framework",
    "ch24-jev-decision-model", "ch23-future-summary",
]


def fetch(name: str) -> bytes:
    url = BASE + name + ".html"
    req = urllib.request.Request(url, headers={"User-Agent": "native-ai-organ/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main() -> int:
    check_only = "--check" in sys.argv
    CACHE.mkdir(parents=True, exist_ok=True)
    old = {}
    if FINGERPRINT.exists():
        old = {c["file"]: c for c in json.loads(FINGERPRINT.read_text())["chapters"]}
    entries, changed = [], []
    for name in CHAPTERS:
        body = fetch(name)
        (CACHE / f"{name}.html").write_bytes(body)
        sha = hashlib.sha256(body).hexdigest()[:16]
        prev = old.get(name, {}).get("sha256")
        status = "new" if prev is None else ("changed" if prev != sha else "same")
        if status != "same":
            changed.append(f"{name}:{status}")
        entries.append({"file": name, "sha256": sha, "bytes": len(body), "status": status})
    if check_only:
        # Routine drift check: report only, never rewrite the fingerprint baseline.
        print(f"Check: {len(entries)} chapters vs {FINGERPRINT.relative_to(ROOT)}")
        if changed:
            print("DRIFT:", ", ".join(changed))
            print("Run without --check to refresh cache + fingerprint, then re-parse:")
            print("  python3 scripts/fetch-aag.py && python3 scripts/parse-aag.py")
            return 1
        print("No content changes since last fingerprint.")
        return 0
    fp = {
        "source": "https://ai-agent-guide.xiaofuge.cn/",
        "repo": "https://github.com/fuzhengwei/ai-agent-guide",
        "fetched": str(date.today()),
        "chapter_count": len(entries),
        "chapters": entries,
    }
    FINGERPRINT.parent.mkdir(parents=True, exist_ok=True)
    FINGERPRINT.write_text(json.dumps(fp, ensure_ascii=False, indent=2) + "\n")
    print(f"Fetched {len(entries)} chapters -> {CACHE.relative_to(ROOT)}")
    print(f"Fingerprint -> {FINGERPRINT.relative_to(ROOT)}")
    if changed:
        print("Changed:", ", ".join(changed))
    else:
        print("No content changes since last fingerprint.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
