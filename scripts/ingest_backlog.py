#!/usr/bin/env python3
"""
从 inbox/ 目录按日期收集 *.txt 作为当天日报的“收件箱”补充条目。

规则：
- 文件命名：YYYY-MM-DD_*.txt （默认处理当天日期，可用 --date 指定）
- 将文件第一行视为标题，其余内容为内容正文（可为空）
- 若 `daily_reports/YYYY-MM-DD.md` 不存在，会先创建一个最小日报再追加“收件箱”部分

用法：
  python scripts/ingest_backlog.py            # 处理今天
  python scripts/ingest_backlog.py --date 2025-10-16
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv

from utils import ensure_dir


def find_inbox_files(inbox_dir: Path, date_str: str) -> List[Path]:
    if not inbox_dir.exists():
        return []
    pattern = f"{date_str}_*.txt"
    return sorted(inbox_dir.glob(pattern))


def parse_note(path: Path) -> Tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        return path.stem, ""
    lines = text.splitlines()
    title = lines[0].strip() or path.stem
    body = "\n".join(lines[1:]).strip()
    return title, body


def ensure_minimal_report(report_path: Path, date_str: str) -> None:
    if report_path.exists():
        return
    ensure_dir(str(report_path.parent))
    content = f"# AI 情报日报 - {date_str}\n\n(自动创建的最小日报，等待补充)\n\n"
    report_path.write_text(content, encoding="utf-8")


def append_inbox_section(report_path: Path, date_str: str, items: List[Tuple[str, str]]) -> None:
    if not items:
        return
    section_lines: List[str] = []
    section_lines.append("## 收件箱补充")
    section_lines.append("")
    for title, body in items:
        section_lines.append(f"- {title}")
        if body:
            section_lines.append("")
            section_lines.append(f"  {body}")
            section_lines.append("")
    with report_path.open("a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(section_lines).rstrip() + "\n")


def main() -> int:
    if os.path.exists(".env"):
        load_dotenv(".env")

    parser = argparse.ArgumentParser(description="Ingest inbox notes into daily report")
    parser.add_argument("--date", help="YYYY-MM-DD, default=today")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    inbox_dir = Path("inbox")
    report_path = Path("daily_reports") / f"{date_str}.md"

    files = find_inbox_files(inbox_dir, date_str)
    if not files:
        print(f"[INFO] No inbox notes found for {date_str} in {inbox_dir}")
        return 0

    ensure_minimal_report(report_path, date_str)

    items: List[Tuple[str, str]] = [parse_note(p) for p in files]
    append_inbox_section(report_path, date_str, items)
    print(f"[OK] Ingested {len(items)} notes into {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

