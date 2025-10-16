# 贡献指南

欢迎为 AI 情报仓库做出贡献！

## 贡献方式

### 1. 添加信息源
- 在 `/sources/` 目录下添加新的信息源
- 确保信息源可靠且更新频繁
- 按照现有格式进行分类

### 2. 改进算法
- 优化日报生成逻辑
- 改进快讯关键词检测
- 增强时区处理

### 3. 修复问题
- 报告 Bug 并提供复现步骤
- 提交 Pull Request 修复问题

### 4. 新功能建议
- 在 Issues 中提出新功能建议
- 详细描述使用场景

## 提交规范

### 提交信息格式
```
<type>: <description>

[optional body]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Type 类型
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

## 开发环境设置

1. Fork 本仓库
2. 克隆到本地
3. 创建分支：`git checkout -b feature/your-feature`
4. 安装依赖：`pip install -r scripts/requirements.txt`
5. 提交更改
6. 推送分支：`git push origin feature/your-feature`
7. 创建 Pull Request

## 代码规范

- Python 代码遵循 PEP 8
- 使用有意义的变量名
- 添加必要的注释
- 确保脚本可以在 GitHub Actions 中正常运行

---

感谢您的贡献！🚀
