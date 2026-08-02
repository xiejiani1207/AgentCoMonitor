# CLAUDE.md — AgentCoMonitor

跨智能体协同执行智能监控与结果筛选优化系统

## 项目红线

- `.env` 绝不提交到 git（含真实 Neon 密码和 LLM API Key）
- Push 前必须 `ruff check` + `pytest` 全绿
- 数据库迁移只通过 Alembic（不手改 schema）
- `demo_advisory/` 不 import `agent_monitor`（Demo 零侵入原则）

## 常用命令

```bash
make test              # 全部测试（25 个）
make lint              # ruff 检查
make migrate           # 运行数据库迁移
python demo_pipeline.py  # 跑监控链路 Demo
python demo_advisory/graph.py  # 跑投顾全链路 Demo
uvicorn agent_monitor.api.main:app --reload  # 启动 API
```

## 技术栈速查

| 组件 | 技术 |
|------|------|
| 数据库 | PostgreSQL（Neon 免费层） |
| 监控 LLM | OpenAI 兼容接口（AM_LLM_*） |
| Demo LLM | OpenAI 兼容接口（DEMO_LLM_*，回退 AM_LLM_*） |
| CI | GitHub Actions（push → test + lint） |
| Lint | ruff（版本需≥0.15，pyproject.toml 已配置豁免规则） |

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

## API 层（agent_monitor/api/）

- main.py：FastAPI 入口 + CORS
- routes.py：13 个 REST 端点（tasks/traces/anomalies/quality/suggestions）+ WebSocket
- schemas.py：Pydantic 响应模型
- websocket.py：WebSocket 连接管理 + 广播

## Demo 系统（demo_advisory/）

- 6 Agent LangGraph 链路：数据采集 → 技术面 ∥ 基本面 → 风控 → 决策 → 合规
- yfinance 真实 A 股数据（5 只股票，60 天日线）
- System Prompt 5 份
- 公共 LLM 模块（_llm.py，优先 DEMO_LLM_*，回退 AM_LLM_*）

## 深入文档

| 文档 | 路径 |
|------|------|
| 完整设计 | docs/superpowers/specs/2026-07-10-agent-monitoring-system-design.md |
| 精炼设计 | docs/superpowers/specs/2026-07-10-design-summary.md |
| 项目规划 | planning/task_plan.md |
| 进度日志 | planning/progress.md |
| 踩坑记录 | planning/findings.md |
