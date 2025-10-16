#!/usr/bin/env python3
import os, sys, argparse, re
from datetime import datetime
from utils import ensure_dir

def parse_date_from_name(name):
    m = re.search(r'(20\d{2}-\d{2}-\d{2})', name)
    return m.group(1) if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inbox', help='历史片段目录（.md/.txt）')
    ap.add_argument('--append', action='store_true')
    args = ap.parse_args()

    ensure_dir('daily_reports')

    for fn in sorted(os.listdir(args.inbox)):
        if not fn.lower().endswith(('.md','.txt')):
            continue
        date = parse_date_from_name(fn)
        if not date:
            print(f'[skip] 无日期：{fn}')
            continue
        src = os.path.join(args.inbox, fn)
        dst = os.path.join('daily_reports', f'{date}.md')
        with open(src, 'r', encoding='utf-8') as f:
            chunk = f.read().strip()
        header = f"\n\n---\n> [imported from inbox/{fn}]\n\n"
        if os.path.exists(dst):
            with open(dst, 'a', encoding='utf-8') as g:
                g.write(header)
                g.write(chunk)
        else:
            with open(dst, 'w', encoding='utf-8') as g:
                g.write(f"# AI 日报｜{date}（CST）\n")
                g.write(header)
                g.write(chunk)
        print(f'[ok] {fn} -> {dst}')

if __name__ == '__main__':
    main()
