# 历史 backlog 导入说明

你可将历史 ChatGPT 对话中沉淀的情报（日报片段、源清单、规则、成就等）按下列方式导入：

1. 将原始片段粘贴到 `inbox/`（自建临时目录，不纳入版本控制）。
2. 运行：`python scripts/ingest_backlog.py inbox/ --append`。
3. 脚本会自动：
   - 去重（同源链接/同标题同日只保留最新一条）。
   - 按 `/config/classification_schema.md` 分类。
   - 根据日期写入 `/daily_reports/YYYY-MM-DD.md`。
4. 手动检查并提交。
