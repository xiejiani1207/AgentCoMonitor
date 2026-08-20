# 开发文档

## 1. 开发环境

| 依赖 | 版本要求 |
|------|----------|
| Python | ≥ 3.11 |
| Node.js | ≥ 18（推荐 20+） |
| PostgreSQL | 免费层 Neon（或本地 Docker） |
| 包管理 | pip + npm |
| Lint | ruff ≥ 0.15（本项目锁 0.16.1） |

## 2. 环境搭建

```bash
# 1. 克隆
git clone https://github.com/xiejiani1207/AgentCoMonitor.git
cd AgentCoMonitor

# 2. 配置环境变量（复制模板，填入 DB 连接 + LLM key）
cp .env.example .env

# 3. 安装后端依赖
pip install -e ".[dev]"        # 含 ruff、pytest

# 4. 安装前端依赖
cd dashboard && npm install && cd ..

# 5. 数据库迁移
alembic upgrade head
```

## 3. 项目结构

见 `docs/design.md` 第 2 节「代码组织」。

## 4. 本地运行

### 4.1 三个服务
```bash
# 终端 1：监控服务（:8000）
uvicorn agent_monitor.api.main:app --reload

# 终端 2：投顾服务（:8001）
uvicorn demo_service.main:app --port 8001

# 终端 3：前端（:3000）
cd dashboard && npm run dev
```

### 4.2 命令行 Demo（无需前端）
```bash
python demo_pipeline.py                       # 监控链路演示（内存）
python run_monitored_demo.py                  # 端到端监控演示（落库）
python demo_advisory/graph.py                 # 投顾链路独立运行
```

## 5. 测试

```bash
make test            # 全部测试（25 个）
make test-unit       # 单元测试
make test-integration# 集成测试
make lint            # ruff 代码检查
```

测试分层：
- `tests/unit/`：核心模块单元测试（anomaly/quality/optimizer/collector/db models）
- `tests/integration/`：完整链路集成测试（含 DB roundtrip，指向 neon.tech 时自动跳过）

## 6. 数据库迁移

只通过 Alembic，不手改 schema：

```bash
alembic revision --autogenerate -m "描述"   # 生成迁移
alembic upgrade head                        # 应用迁移
alembic current                             # 查看当前版本
```

当前迁移：`001_initial_schema`（5 张核心表）+ `002_agent_instructions`（反馈指令库）。

## 7. CI/CD

GitHub Actions（`.github/workflows/test.yml`），push 自动触发：
- **test job**：PostgreSQL 服务容器 + `alembic upgrade head` 迁移验证 + 单元/集成测试
- **lint job**：ruff 检查（版本锁 0.16.1）
- **dashboard job**：`npm ci` + `tsc` 类型检查 + vite build

## 8. 编码规范

1. **零侵入原则**：`demo_advisory/` 不 import `agent_monitor`。
2. **敏感信息**：`.env` 绝不提交（含真实 Neon 密码和 LLM Key）。
3. **Push 门禁**：`ruff check` + `pytest` 全绿。
4. **ruff 配置**：`pyproject.toml` 中豁免 B008（FastAPI Depends）、BLE001（Demo LLM fallback）、DTZ（测试 naive datetime）等。
5. **Agent 返回值**：LangGraph 节点只返回新字段，不复制整个 state（避免并行分支 State 冲突）。

## 9. 常见踩坑

详见 `planning/findings.md`，关键几条：
- **ruff CI 版本不一致**：本地/CI 需锁同版本，本项目已在 dev extras 锁 `ruff==0.16.1`。
- **LangGraph 并行分支 State 冲突**：node 只返回新字段。
- **Windows + asyncpg + Neon SSL**：async 连接用 `?ssl=require`。
- **LangGraph 1.x 适配器**：节点事件走 `astream_events`，旧 `config["callbacks"]` 回调 `serialized=None`。
- **alembic.ini 编码**：Windows GBK 无法读 UTF-8 中文注释，ini 文件用 ASCII。
- **Vite 代理与 SPA 路由冲突**：API 路径（`/advisory`）与页面路由（`/chat`）需分开，否则 GET 导航被代理劫持。
