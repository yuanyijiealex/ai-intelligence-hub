#!/usr/bin/env python3
"""
快速关键词告警：扫描当天日报（或指定文件）中包含的关键词并输出命中清单。

用法：
  python scripts/quick_alert.py            # 扫描 daily_reports/YYYY-MM-DD.md
  python scripts/quick_alert.py -f path.md # 扫描指定文件
  python scripts/quick_alert.py -o alerts.md  # 额外输出到文件
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


def main() -> int:
    if os.path.exists(".env"):
        load_dotenv(".env")

    parser = argparse.ArgumentParser(description="Quick keyword alert scanner")
    parser.add_argument("-f", "--file", help="file to scan, default is today's report")
    parser.add_argument("-o", "--output", help="optional output file path")
    args = parser.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    default_report = Path("daily_reports") / f"{today}.md"
    target = Path(args.file) if args.file else default_report

    if not target.exists():
        print(f"[WARN] File not found: {target}")
        return 1

    keywords = load_keywords(Path("config/alerts_keywords.yml"))
    if not keywords:
        print("[INFO] No keywords configured. Edit config/alerts_keywords.yml")

    content = target.read_text(encoding="utf-8", errors="ignore")
    hits = scan_text(content, keywords)

    report_lines = [f"# 关键词告警 - {today}", ""]
    report_lines.append(f"目标文件：{target}")
    report_lines.append("")
    if hits:
        report_lines.extend(hits)
    else:
        report_lines.append("- 未命中任何关键词")

    output_md = "\n".join(report_lines) + "\n"
    print(output_md)

    if args.output:
        out_path = Path(args.output)
        ensure_dir(str(out_path.parent))
        out_path.write_text(output_md, encoding="utf-8")
        print(f"[INFO] Alerts written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

