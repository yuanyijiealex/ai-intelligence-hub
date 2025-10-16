#!/usr/bin/env python3
import argparse
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import feedparser
import yaml

from utils import ensure_dir, now_utc, today_strings


def load_sources(config_path: Path) -> List[Dict[str, Any]]:
    if not config_path.exists():
        raise FileNotFoundError(f"Sources config not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return data.get("sources", [])


def build_source_tags_map(sources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    m: Dict[str, List[str]] = {}
    for s in sources:
        name = s.get("name")
        if not name:
            continue
        tags = s.get("tags") or []
        m[str(name)] = list(tags)
    return m


def parse_entry_datetime(entry: Dict[str, Any]) -> Optional[datetime]:
    for key in ("published_parsed", "updated_parsed"):
        if entry.get(key):
            t = entry[key]
            try:
                return datetime(
                    year=t.tm_year,
                    month=t.tm_mon,
                    day=t.tm_mday,
                    hour=t.tm_hour,
                    minute=t.tm_min,
                    second=t.tm_sec,
                    tzinfo=timezone.utc,
                )
            except Exception:
                continue
    return None


TAG_RE = re.compile(r"<[^>]+>")


def plain_text(s: str, max_len: int = 400) -> str:
    s = TAG_RE.sub(" ", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


def load_alert_keywords(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("alerts", [])


def pick_highlights(
    grouped_items: List[Tuple[str, List[Dict[str, Any]]]],
    alerts: List[Dict[str, Any]],
    limit: int = 5,
) -> List[str]:
    # Flatten items with source name
    all_items: List[Tuple[Dict[str, Any], str]] = []
    for source_name, items in grouped_items:
        for it in items:
            all_items.append((it, source_name))

    # Build lower-case keyword list
    keys: List[Tuple[str, List[str]]] = []  # (keyword, tags)
    for a in alerts:
        k = str(a.get("keyword", "")).strip()
        if not k:
            continue
        tags = a.get("tags") or []
        keys.append((k.lower(), tags))

    scored: List[Tuple[int, datetime, Dict[str, Any], str, List[str]]] = []
    for it, src in all_items:
        text = f"{it.get('title','')} {it.get('summary','')}".lower()
        matched_keywords: List[str] = []
        for k, _tags in keys:
            if k and k in text:
                matched_keywords.append(k)
        score = len(set(matched_keywords))
        if score > 0:
            when = it.get("dt") or now_utc()
            scored.append((score, when, it, src, matched_keywords))

    # Sort by score desc then time desc
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top = scored[:limit]

    lines: List[str] = []
    for score, when, it, src, mkeys in top:
        title = it.get("title") or "(无标题)"
        link = it.get("link") or ""
        tag_str = ", ".join(sorted(set(mkeys))) if mkeys else ""
        time_str = when.strftime("%Y-%m-%d %H:%M UTC")
        extra = f" · 关键词: {tag_str}" if tag_str else ""
        lines.append(f"- [{title}]({link}) · 来源: {src} · 时间: {time_str}{extra}")
    return lines


def make_markdown_report(
    date_str: str,
    grouped_items: List[Tuple[str, List[Dict[str, Any]]]],
    window_hours: int,
    highlights: Optional[List[str]] = None,
    column_groups: Optional[List[Tuple[str, List[Dict[str, Any]]]]] = None,
) -> str:
    lines: List[str] = []
    lines.append(f"# AI 情报日报 - {date_str}")
    lines.append("")
    lines.append(f"> 抓取窗口：近 {window_hours} 小时（按 UTC 过滤）")
    lines.append("")
    lines.append("## 今日要点")
    if highlights:
        lines.extend(highlights)
    else:
        lines.append("- （自动摘要占位）")
    total = sum(len(items) for _, items in grouped_items)
    lines.append("")
    # 资讯分栏
    lines.append("## 资讯分栏")
    if column_groups is not None:
        for col_name, items in column_groups:
            lines.append(f"### {col_name} ({len(items)})")
            lines.append("")
            if items:
                for it in items:
                    title = it.get("title") or "(无标题)"
                    link = it.get("link") or ""
                    src = it.get("source") or ""
                    dt = it.get("dt")
                    dt_str = dt.strftime("%Y-%m-%d %H:%M UTC") if isinstance(dt, datetime) else ""
                    lines.append(f"- [{title}]({link}) · 来源: {src}{(' · ' + dt_str) if dt_str else ''}")
                lines.append("")
            else:
                lines.append("- （暂无）\n")
    else:
        lines.append("（暂无分栏数据）\n")

    # 来源分组
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
    start_tag = "<!--LATEST_START-->"
    end_tag = "<!--LATEST_END-->"
    latest_line = f"最新日报：[{date_str}]({link})"

    if not readme_path.exists():
        content = [
            "AI 情报仓库（AI Intelligence Hub）",
            "",
            "最新日报",
            start_tag,
            latest_line,
            end_tag,
            "",
        ]
        readme_path.write_text("\n".join(content), encoding="utf-8")
        return

    text = readme_path.read_text(encoding="utf-8")
    s = text.find(start_tag)
    e = text.find(end_tag)
    if s != -1 and e != -1 and s < e:
        new_text = text[: s + len(start_tag)] + "\n" + latest_line + "\n" + text[e:]
        readme_path.write_text(new_text, encoding="utf-8")
    else:
        with readme_path.open("a", encoding="utf-8") as f:
            f.write("\n最新日报\n")
            f.write(start_tag + "\n")
            f.write(latest_line + "\n")
            f.write(end_tag + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate AI daily intelligence report")
    parser.add_argument("--hours", type=int, default=None, help="Time window in hours (override env)")
    args = parser.parse_args()

    # env
    window_hours = args.hours if args.hours is not None else int(os.getenv("REPORT_TIME_WINDOW_HOURS", "24"))
    max_items_per_source = int(os.getenv("MAX_ITEMS_PER_SOURCE", "20"))
    http_timeout = int(os.getenv("HTTP_TIMEOUT", "15"))
    user_agent = os.getenv("USER_AGENT", "ai-intelligence-hub/1.0")

    # time window
    now = now_utc()
    window_start = now - timedelta(hours=window_hours)

    # sources
    sources = load_sources(Path("config/sources.yml"))
    source_tags_map = build_source_tags_map(sources)

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
            headers = {
                "User-Agent": user_agent,
                "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
            }
            resp = requests.get(url, headers=headers, timeout=http_timeout)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[: max_items_per_source]:
                dt = parse_entry_datetime(entry)
                if dt is None or dt < window_start:
                    continue
                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()
                summary = plain_text(entry.get("summary") or entry.get("description") or "")
                items.append({"title": title, "link": link, "summary": summary, "dt": dt})
        except Exception as e:
            items.append({
                "title": f"[抓取失败] {name}",
                "link": url,
                "summary": f"错误：{e}",
                "dt": now,
            })
        collected.append((name, items))

    # highlights by keyword alerts
    alerts = load_alert_keywords(Path("config/alerts_keywords.yml"))
    highlights = pick_highlights(collected, alerts, limit=5)

    # build column groups by source tags
    def categorize(tags: List[str], src_name: str) -> str:
        tset = {t.lower() for t in (tags or [])}
        name_l = (src_name or "").lower()
        # 大模型与平台：匹配常见厂商或标签
        if any(k in name_l for k in ["openai", "hugging face", "anthropic", "google ai", "deepmind", "meta ai", "stability"]):
            return "大模型与平台"
        if {"llm", "platform"} & tset:
            return "大模型与平台"
        if {"research", "arxiv"} & tset:
            return "研究与论文"
        if {"company"} & tset:
            return "公司与产品"
        if {"tools"} & tset:
            return "工具与框架"
        return "其他与综合"

    columns_order = ["大模型与平台", "研究与论文", "公司与产品", "工具与框架", "其他与综合"]
    bucket: Dict[str, List[Dict[str, Any]]] = {k: [] for k in columns_order}
    for src_name, items in collected:
        tags = source_tags_map.get(src_name, [])
        col = categorize(tags, src_name)
        for it in items:
            # copy minimal fields + source tag
            bucket[col].append({
                "title": it.get("title"),
                "link": it.get("link"),
                "dt": it.get("dt"),
                "source": src_name,
            })
    column_groups = [(name, bucket.get(name, [])) for name in columns_order]

    # output file uses CST date for user friendliness
    _, cst_date = today_strings()
    out_dir = Path("daily_reports")
    ensure_dir(str(out_dir))
    out_file = out_dir / f"{cst_date}.md"
    content = make_markdown_report(
        cst_date,
        collected,
        window_hours,
        highlights=highlights if highlights else None,
        column_groups=column_groups,
    )
    out_file.write_text(content, encoding="utf-8")

    update_readme_latest(Path("README.md"), cst_date)

    print(f"Generated report: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
