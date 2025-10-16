# AI Intelligence Hub 🤖

AI 情报仓库 - 自动化 AI 日报与重大事件快讯生成系统

## 功能特色
- 🤖 **自动日报生成**: 每日 09:00 / 21:00 (CST) 自动生成 AI 行业日报
- ⚡ **重大事件快讯**: 关键词触发，即时生成并插入日报顶部
- 🌍 **时区支持**: 上海时区 (UTC+8)，支持双时区显示
- 📊 **信息源管理**: 模块化信息源配置，支持多种数据源
- 🔄 **自动化工作流**: GitHub Actions 完全自动化的 CI/CD 流程

## 快速开始
```bash
# 克隆仓库
git clone https://github.com/yuanyijiealex/ai-intelligence-hub.git
cd ai-intelligence-hub

# 安装依赖
pip install -r scripts/requirements.txt

# 测试运行
python scripts/generate_report.py --date 2025-10-16
```

## 目录结构
```
ai-intelligence-hub/
├── 📁 daily_reports/     # 生成的日报文件
├── 📁 scripts/           # 核心脚本和工具
├── 📁 config/            # 配置文件和规则
├── 📁 sources/           # 信息源配置
├── 📁 templates/         # 报告模板
├── 📁 inbox/             # 快讯触发文件
└── 📁 .github/workflows/ # GitHub Actions 配置
```

## 核心组件
- **scripts/generate_report.py**: 日报生成主脚本
- **scripts/quick_alert.py**: 快讯检测和生成
- **config/alerts_keywords.yml**: 快讯关键词配置
- **.github/workflows/daily-digest.yml**: 自动化工作流

## 快讯系统
当 `inbox/` 目录中的文件包含以下关键词时，会自动生成快讯：
- 🚀 **新模型/版本**: 发布、GPT、Claude、Gemini 等
- 📖 **开源/SOTA**: 开源、SOTA、state of the art 等
- 💰 **价格/商业策略**: 降价、订阅、pro、enterprise 等
- 🔥 **生态破圈**: 爆火、刷屏、trending 等

## 免责声明
本仓库仅做信息聚合与学习研究用途，来源链接归原站点所有。

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)