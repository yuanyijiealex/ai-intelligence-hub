#!/usr/bin/env python3
from __future__ import annotations

import os, re, argparse, datetime as dt, yaml
from pathlib import Path

KW_FILE = "config/alerts_keywords.yml"
TEMPLATE = "# 【快讯】{title}｜{date_cst}\n- 事件：{summary}\n- 影响：{impact}\n- 参考：{refs}\n"


def load_keywords():
    path = Path(KW_FILE)
    if not path.exists():
        return []
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    flags = re.IGNORECASE if cfg.get("ignore_case", True) else 0
    groups = []
    # Preferred: groups with regex patterns
    for g in cfg.get("groups", []) or []:
        pats = [re.compile(p, flags) for p in g.get("patterns", [])]
        groups.append((g.get("name", "misc"), pats))
    if groups:
        return groups
    # Fallback: alerts list with plain keywords
    alerts = cfg.get("alerts", []) or []
    if alerts:
        pats = [re.compile(re.escape(str(a.get("keyword", "")).strip()), flags) for a in alerts if str(a.get("keyword", "")).strip()]
        if pats:
            groups.append(("keywords", pats))
    return groups


def scan_inbox_for_alerts():
    inbox = Path("inbox")
    if not inbox.exists():
        return []
    files = sorted([*inbox.glob("*.md"), *inbox.glob("*.txt")])
    return files[-10:]


def detect_alerts(text, groups):
    hits = []
    for gname, pats in groups:
        for pat in pats:
            if pat.search(text):
                hits.append((gname, pat.pattern))
    return hits


def prepend_to_daily(date_cst, content):
    path = Path("daily_reports") / f"{date_cst}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# AI 日报｜{date_cst}（CST）\n\n", encoding="utf-8")
    original = path.read_text(encoding="utf-8")
    path.write_text(content + "\n\n" + original, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="CST 日期 YYYY-MM-DD；默认今日")
    args = ap.parse_args()
    if args.date:
        date_cst = args.date
    else:
        date_cst = (dt.datetime.utcnow() + dt.timedelta(hours=8)).strftime("%Y-%m-%d")

    groups = load_keywords()
    candidates = scan_inbox_for_alerts()
    compiled_alerts = []

    for p in candidates:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        hits = detect_alerts(txt, groups)
        if hits:
            stem = p.stem
            title = (stem[:60] + "...") if len(stem) > 60 else stem
            urls = re.findall(r"https?://\S+", txt)
            refs = ", ".join(urls[:3]) if urls else "无"
            groups_hit = ", ".join(sorted({h[0] for h in hits}))
            summary = f"命中关键词 {len(hits)} 项（{groups_hit}）"
            impact = "高关注度事件，建议优先跟进"
            alert_md = TEMPLATE.format(title=title, date_cst=date_cst, summary=summary, impact=impact, refs=refs)
            compiled_alerts.append(alert_md)

    if compiled_alerts:
        banner = ">\n> **[重大事件快讯聚合]** 以下内容由关键词自动触发，需复核。\n>\n"
        prepend_to_daily(date_cst, banner + "\n".join(compiled_alerts))
        print(f"[ok] quick alerts appended to daily_reports/{date_cst}.md")
    else:
        print("[info] no alerts found")


if __name__ == "__main__":
    main()
