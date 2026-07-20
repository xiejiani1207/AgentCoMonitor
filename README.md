# AgentCoMonitor

跨智能体协同执行智能监控与结果筛选优化系统

## 项目结构

```
agent_monitor/          # Part 1: 通用监控平台（核心交付）
├── core/
│   ├── models.py       # TraceRecord 通用数据模型
│   ├── collector.py    # 模块一：执行监控采集
│   ├── anomaly.py      # 模块二：异常检测（三层扫描）
│   ├── quality.py      # 模块三：质量评估（五维度 + LLM-as-Judge）
│   ├── optimizer.py    # 模块四：结果筛选优化
│   └── llm_client.py   # LLM 客户端（OpenAI 兼容接口）
├── adapters/
│   ├── base.py         # MonitoringAdapter 抽象接口
│   └── langgraph.py    # LangGraph 适配器
├── api/                # FastAPI + WebSocket（待实现）
├── db/
│   ├── models.py       # 5 张 ORM 表
│   ├── session.py      # 异步会话 + Neon SSL
│   └── migrations/     # Alembic
└── config.py           # pydantic-settings

demo_advisory/          # Part 2: 金融投顾 Demo（待实现）
├── agents/             # 6 个业务 Agent
├── mock_data/          # Mock 股票数据
└── prompts/            # System Prompt 模板

dashboard/              # Web 前端 (Phase 4)
tests/                  # 25 个测试（16 单元 + 2 集成 + LLM）
docs/                   # 设计文档
```

## 快速开始

```bash
git clone https://github.com/xiejiani1207/AgentCoMonitor.git
cd AgentCoMonitor
cp .env.example .env          # 编辑填入 DB 连接和 LLM API Key
pip install -e ".[dev,ml]"
make migrate                   # 初始化数据库
python demo_pipeline.py        # 跑 Demo 验证全链路
```

## 测试与 CI

```bash
make test        # 全部测试（25 个）
make test-unit   # 单元测试
make lint        # ruff 代码检查
```

CI/CD: GitHub Actions — push 自动跑 test + lint。

## 技术栈

| 层级 | 技术 |
|------|------|
| Agent 框架 | LangGraph (待对接 Demo) |
| 后端 | Python + FastAPI |
| 前端 | React + TypeScript + AntV G6 + ECharts (Phase 4) |
| 数据库 | PostgreSQL (Neon 免费层 / Docker) |
| LLM | OpenAI 兼容接口 (DeepSeek / GPT) |
| CI/CD | GitHub Actions |
