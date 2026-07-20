# CLAUDE.md — AgentCoMonitor

跨智能体协同执行智能监控与结果筛选优化系统

## 项目红线

- `.env` 绝不提交到 git（含真实 Neon 密码和 LLM API Key）
- Push 前必须 `ruff check` + `pytest` 全绿
- 数据库迁移只通过 Alembic（不手改 schema）
- `demo_advisory/` 不 import `agent_monitor`（Demo 零侵入原则）

## 常用命令

```bash
make test              # 全部测试
make lint              # ruff 检查
make migrate           # 运行数据库迁移
python demo_pipeline.py  # 跑 Demo 验证全链路
```

## 技术栈速查

| 组件 | 技术 |
|------|------|
| 数据库 | PostgreSQL（Neon 免费层） |
| LLM | OpenAI 兼容接口（当前：DeepSeek deepseek-chat） |
| CI | GitHub Actions（push → test + lint） |

## 核心模块（agent_monitor/core/）

| 模块 | 文件 | 职责 |
|------|------|------|
| 监控采集 | collector.py | TraceRecord → PostgreSQL + WebSocket |
| 异常检测 | anomaly.py | 三层扫描（执行/行为/输出） |
| 质量评估 | quality.py | 五维度 + LLM-as-Judge |
| 筛选优化 | optimizer.py | 四步 Pipeline + 双通道建议 |
| LLM 客户端 | llm_client.py | OpenAI 兼容接口 |

## 适配器（agent_monitor/adapters/）

- base.py：MonitoringAdapter 抽象接口
- langgraph.py：LangGraph callbacks 零侵入适配

## 深入文档

| 文档 | 路径 |
|------|------|
| 完整设计 | docs/superpowers/specs/2026-07-10-agent-monitoring-system-design.md |
| 精炼设计 | docs/superpowers/specs/2026-07-10-design-summary.md |
| 项目规划 | planning/task_plan.md |
| 进度日志 | planning/progress.md |
