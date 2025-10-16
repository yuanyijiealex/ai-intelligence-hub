#!/usr/bin/env python3
import os, sys, argparse, datetime as dt, subprocess
from utils import ensure_dir, now_utc, utc_to_cst

TEMPLATE = """# AI 日报｜{date_cst}（CST）
## 今日要点
- （自动摘要占位）

## 资讯分栏
### 1. 大模型与平台
- （暂无）
### 2. 开源生态
- （暂无）
### 3. 论文与基准
- （暂无）
### 4. 工程与工具链
- （暂无）
### 5. 商业与生态
- （暂无）
### 6. 其他与综合
- （暂无）

---
*UTC: {utc} · CST: {cst}*
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', help='生成指定 CST 日期 YYYY-MM-DD')
    args = ap.parse_args()

    if args.date:
        date_cst = args.date
        utc = dt.datetime.strptime(date_cst, '%Y-%m-%d') - dt.timedelta(hours=8)
        cst = utc + dt.timedelta(hours=8)
    else:
        utc = now_utc(); cst = utc_to_cst(utc)
        date_cst = cst.strftime('%Y-%m-%d')

    out_dir = os.path.join('daily_reports')
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, f'{date_cst}.md')

    content = TEMPLATE.format(
        date_cst=date_cst,
        utc=utc.strftime('%Y-%m-%d %H:%M'),
        cst=cst.strftime('%Y-%m-%d %H:%M')
    )

    if os.path.exists(out_path):
        with open(out_path, 'a', encoding='utf-8') as f:
            f.write('\n\n> [append] 追加生成占位，等待抓取器填充\n')
    else:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)

    print(f'Generated: {out_path}')
    try:
        subprocess.run([sys.executable, 'scripts/quick_alert.py', '--date', date_cst], check=False)
    except Exception as e:
        print(f'[warn] quick_alert skipped: {e}')

if __name__ == '__main__':
    main()

