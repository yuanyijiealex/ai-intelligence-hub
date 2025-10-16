AI 情报仓库（AI Intelligence Hub）

概览
- 定时抓取主流 AI/研究/公司博客 RSS 源
- 生成每日 Markdown 日报并提交到仓库 `daily_reports/`
- GitHub Actions 每天自动运行并推送最新日报
- 可本地运行，支持时区、抓取窗口等配置

快速开始（本地）
1) 安装 Python 3.11+
2) 创建并激活虚拟环境（可选）
   - Windows (PowerShell): `python -m venv .venv; . .venv/Scripts/Activate.ps1`
   - macOS/Linux (bash): `python -m venv .venv; source .venv/bin/activate`
3) 安装依赖：`pip install -r scripts/requirements.txt`
4) 复制 `.env.example` 为 `.env`，按需调整变量（如时区）
5) 运行：`python scripts/generate_report.py`

运行效果
- 首次运行会在 `daily_reports/` 生成 `YYYY-MM-DD.md` 日报，并更新本文件“最新日报”区块。
- Git 变更由工作流自动提交；本地运行时需自行 `git add/commit/push`。

配置
- `.env`（示例见 `.env.example`）
  - `TIMEZONE`：默认 `Asia/Shanghai`
  - `REPORT_TIME_WINDOW_HOURS`：抓取近多少小时内的更新，默认 24
  - `MAX_ITEMS_PER_SOURCE`：每个源最多条目，默认 20
  - `HTTP_TIMEOUT`：HTTP 超时秒数，默认 15
  - `USER_AGENT`：抓取 UA，默认 `ai-intelligence-hub/1.0`
- `config/sources.yml`：RSS 源清单，可按需增删

GitHub Actions
- 工作流文件：`.github/workflows/daily-digest.yml`
- 默认每天 00:00 UTC 运行（北京时间 08:00）
- 会在有变更时自动提交：提交信息形如 `chore: daily report YYYY-MM-DD`

最新日报
<!--LATEST_START-->
最新日报：[2025-10-16](daily_reports/2025-10-16.md)
<!--LATEST_END-->

常见问题
- 某些源不可用：脚本会跳过失败源并在日志中标注。
- 报时与时区：使用 `TIMEZONE` 控制“当天”定义，默认中国时区。
- 行尾符警告：如在 Windows 出现 CRLF/LF 警告，不影响功能。

