#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import feedparser
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from utils import ensure_dir, get_env, http_get, normalize_url, utcnow


def load_sources(config_path: Path) -> List[Dict[str, Any]]:
    if not config_path.exists():
        raise FileNotFoundError(f"Sources config not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return data.get("sources", [])


def parse_entry_datetime(entry: Dict[str, Any]) -> Optional[datetime]:
    # Prefer published -> updated -> None
    for key in ("published_parsed", "updated_parsed"):
        if entry.get(key):
            t = entry[key]
            try:
                dt = datetime(
                    year=t.tm_year,
                    month=t.tm_mon,
                    day=t.tm_mday,
                    hour=t.tm_hour,
                    minute=t.tm_min,
                    second=t.tm_sec,
                    tzinfo=timezone.utc,
                )
                return dt
            except Exception:
                continue
    return None


def extract_text(html: str, max_len: int = 400) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    text = " ".join(soup.get_text(" ").split())
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def make_markdown_report(
    date_str: str,
    timezone_name: str,
    grouped_items: List[Tuple[str, List[Dict[str, Any]]]],
    window_hours: int,
) -> str:
    lines: List[str] = []
    lines.append(f"# AI 情报日报 - {date_str}")
    lines.append("")
    lines.append(f"> 时区：{timezone_name} | 抓取窗口：近 {window_hours} 小时")
    total = sum(len(items) for _, items in grouped_items)
    lines.append("")
    lines.append(f"共收录 {total} 条更新，按来源分组如下：")
    lines.append("")
    for source_name, items in grouped_items:
        if not items:
            continue
        lines.append(f"## {source_name} ({len(items)})")
        lines.append("")
        for it in items:
            title = it.get("title") or "(无标题)"
            link = it.get("link") or ""
            dt = it.get("dt")
            dt_str = dt.strftime("%Y-%m-%d %H:%M UTC") if isinstance(dt, datetime) else ""
            summary = it.get("summary") or ""
            lines.append(f"- [{title}]({link})  ")
            if dt_str:
                lines.append(f"  - 时间：{dt_str}")
            if summary:
                lines.append(f"  - 摘要：{summary}")
        lines.append("")
    if total == 0:
        lines.append("（今天暂无抓取到更新，可能源未更新或网络异常）")
    return "\n".join(lines).rstrip() + "\n"


def update_readme_latest(readme_path: Path, date_str: str) -> None:
    link = f"daily_reports/{date_str}.md"
    latest_block = (
        "<!--LATEST_START-->",
        f"最新日报：[{date_str}]({link})",
        "<!--LATEST_END-->",
    )
    if not readme_path.exists():
        content = [
            "AI 情报仓库（AI Intelligence Hub）",
            "",
            "最新日报",
            latest_block[0],
            latest_block[1],
            latest_block[2],
            "",
        ]
        readme_path.write_text("\n".join(content), encoding="utf-8")
        return

    text = readme_path.read_text(encoding="utf-8")
    start = text.find(latest_block[0])
    end = text.find(latest_block[2])
    if start != -1 and end != -1 and start < end:
        new_text = text[: start + len(latest_block[0])] + "\n" + latest_block[1] + "\n" + text[end:]
        readme_path.write_text(new_text, encoding="utf-8")
    else:
        # append block
        with readme_path.open("a", encoding="utf-8") as f:
            f.write("\n最新日报\n")
            f.write(latest_block[0] + "\n")
            f.write(latest_block[1] + "\n")
            f.write(latest_block[2] + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate AI daily intelligence report")
    parser.add_argument("--hours", type=int, default=None, help="Time window in hours (override env)")
    args = parser.parse_args()

    # load env
    if os.path.exists(".env"):
        load_dotenv(".env")

    timezone_name = get_env("TIMEZONE", "Asia/Shanghai")
    window_hours = args.hours if args.hours is not None else int(get_env("REPORT_TIME_WINDOW_HOURS", "24"))
    max_items_per_source = int(get_env("MAX_ITEMS_PER_SOURCE", "20"))
    http_timeout = int(get_env("HTTP_TIMEOUT", "15"))
    user_agent = get_env("USER_AGENT", "ai-intelligence-hub/1.0")

    # time window
    now_utc = utcnow()
    window_start = now_utc - timedelta(hours=window_hours)

    # load sources
    sources = load_sources(Path("config/sources.yml"))

    collected: List[Tuple[str, List[Dict[str, Any]]]] = []
    for src in sources:
        if src.get("type") != "rss":
            continue
        name = src.get("name") or "Unknown"
        url = src.get("url")
        if not url:
            continue
        items: List[Dict[str, Any]] = []
        try:
            resp = http_get(url, timeout=http_timeout, user_agent=user_agent)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[: max_items_per_source]:
                dt = parse_entry_datetime(entry)
                if dt is None or dt < window_start:
                    continue
                title = (entry.get("title") or "").strip()
                link = normalize_url(entry.get("link") or "")
                summary = extract_text(entry.get("summary") or entry.get("description") or "")
                items.append({"title": title, "link": link, "summary": summary, "dt": dt})
        except Exception as e:
            # record error as a pseudo item for transparency
            items.append({
                "title": f"[抓取失败] {name}",
                "link": url,
                "summary": f"错误：{e}",
                "dt": now_utc,
            })
        collected.append((name, items))

    # output
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path("daily_reports")
    ensure_dir(str(out_dir))
    out_file = out_dir / f"{date_str}.md"
    content = make_markdown_report(date_str, timezone_name, collected, window_hours)
    out_file.write_text(content, encoding="utf-8")

    # update README latest section
    update_readme_latest(Path("README.md"), date_str)

    print(f"Generated report: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

