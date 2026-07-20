# AgentCoMonitor

跨智能体协同执行智能监控与结果筛选优化系统

## 项目结构

```
AgentCoMonitor/
├── agent_monitor/          # 通用监控平台（核心交付）
│   ├── core/               # 四大监控模块
│   ├── adapters/           # 框架适配器（接口 + LangGraph 实现）
│   ├── api/                # FastAPI + WebSocket
│   └── db/                 # 数据模型 + Alembic 迁移
├── demo_advisory/          # 金融投顾 Demo（被监控对象）
│   ├── agents/             # 6 个业务 Agent
│   ├── mock_data/          # Mock 股票数据
│   └── prompts/            # System Prompt 模板
├── dashboard/              # Web 前端 (React + TypeScript)
├── tests/                  # 测试
│   ├── unit/               # 单元测试
│   └── integration/        # 集成测试
├── docs/                   # 文档
└── planning/               # 项目规划
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repo-url>
cd AgentCoMonitor

# 安装依赖
make install            # 核心依赖
make dev-install        # 含 ML 依赖（sentence-transformers）

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 Neon 数据库连接字符串和 LLM API Key
```

### 2. 数据库

**选项 A：本地 Docker（开发）**
```bash
make db-up
make migrate
```

**选项 B：Neon（生产/Demo）**
在 `.env` 中配置 Neon 连接字符串后：
```bash
make migrate
```

### 3. 运行

```bash
# 启动 API 服务
uvicorn agent_monitor.api.main:app --reload

# 运行 Demo Agent 链
python -m demo_advisory.graph
```

### 4. 测试

```bash
make test                # 全部测试
make test-unit           # 仅单元测试
make lint                # 代码检查
make format              # 代码格式化
```

## 技术栈

| 层级 | 技术 |
|------|------|
| Agent 框架 | LangGraph |
| 后端 | Python + FastAPI |
| 前端 | React + TypeScript + AntV G6 + ECharts |
| 实时通信 | WebSocket |
| 数据库 | PostgreSQL (Neon / Docker) |
| CI/CD | GitHub Actions |
