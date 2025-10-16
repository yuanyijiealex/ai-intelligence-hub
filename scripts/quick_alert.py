#!/usr/bin/env python3
"""
快速关键词告警：扫描日报中的关键词命中，并更新“今日要点”占位。

用法：
  python scripts/quick_alert.py --date 2025-10-16   # 扫描并更新当日文件
  python scripts/quick_alert.py -f path.md          # 扫描指定文件
  python scripts/quick_alert.py -o alerts.md        # 额外输出到文件
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml
from dotenv import load_dotenv

from utils import ensure_dir


def load_keywords(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("alerts", [])


def scan_text(content: str, keywords: List[Dict[str, str]]) -> List[str]:
    hits: List[str] = []
    lowered = content.lower()
    for kw in keywords:
        key = str(kw.get("keyword", "")).strip()
        if not key:
            continue
        if key.lower() in lowered:
            tags = kw.get("tags") or []
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            hits.append(f"- 命中关键词：{key}{tag_str}")
    return hits


def replace_highlights(report_path: Path, lines: List[str]) -> None:
    text = report_path.read_text(encoding="utf-8")
    start = text.find("## 今日要点")
    if start == -1:
        # append a section if missing
        with report_path.open("a", encoding="utf-8") as f:
            f.write("\n## 今日要点\n")
            if lines:
                f.write("\n".join(lines) + "\n")
            else:
                f.write("- 未命中任何关键词\n")
        return

    # find end of section (next '## ' or EOF)
    rest = text[start:]
    next_h2 = rest.find("\n## ")
    if next_h2 == -1:
        head = text[: start]
        body = rest
        tail = ""
    else:
        head = text[: start]
        body = rest[: next_h2]
        tail = rest[next_h2:]

    # replace placeholder line if present, else replace content after header
    body_lines = body.splitlines()
    new_body: List[str] = []
    placeholder_replaced = False
    for i, ln in enumerate(body_lines):
        if ln.strip() == "- （自动摘要占位）":
            placeholder_replaced = True
            if lines:
                new_body.extend(lines)
            else:
                new_body.append("- 未命中任何关键词")
        else:
            new_body.append(ln)

    if not placeholder_replaced:
        # inject lines after the header line
        for idx, ln in enumerate(new_body):
            if ln.strip().startswith("## 今日要点"):
                insert_at = idx + 1
                break
        else:
            insert_at = len(new_body)
        injected = new_body[:insert_at]
        injected.extend(lines if lines else ["- 未命中任何关键词"])
        injected.extend(new_body[insert_at:])
        new_body = injected

    new_text = head + "\n".join(new_body) + tail
    report_path.write_text(new_text, encoding="utf-8")


def main() -> int:
    if os.path.exists(".env"):
        load_dotenv(".env")

    parser = argparse.ArgumentParser(description="Quick keyword alert scanner and updater")
    parser.add_argument("--date", help="YYYY-MM-DD; when set, target daily_reports/<date>.md")
    parser.add_argument("-f", "--file", help="file to scan; overrides --date")
    parser.add_argument("-o", "--output", help="optional extra output file path")
    args = parser.parse_args()

    if args.file:
        target = Path(args.file)
    elif args.date:
        target = Path("daily_reports") / f"{args.date}.md"
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        target = Path("daily_reports") / f"{today}.md"

    if not target.exists():
        print(f"[WARN] File not found: {target}")
        return 1

    keywords = load_keywords(Path("config/alerts_keywords.yml"))
    if not keywords:
        print("[INFO] No keywords configured. Edit config/alerts_keywords.yml")

    content = target.read_text(encoding="utf-8", errors="ignore")
    hits = scan_text(content, keywords)

    # update report in-place
    replace_highlights(target, hits)

    # optional extra output
    if args.output:
        out_path = Path(args.output)
        ensure_dir(str(out_path.parent))
        out_text = "\n".join(hits if hits else ["- 未命中任何关键词"]) + "\n"
        out_path.write_text(out_text, encoding="utf-8")
        print(f"[INFO] Alerts written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
