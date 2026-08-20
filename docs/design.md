# 系统设计文档

## 1. 总体架构

系统由三个进程 + 一个共享数据库构成：

```
┌─────────────────────────────────────────────────────────┐
│              Web Dashboard (React + AntD, :3000)         │
│        概览 / 链路追踪 / 任务详情 / 告警 / 智能投顾          │
└──────────────┬──────────────────────────────┬───────────┘
          /api /ws                      /advisory/chat /ws
┌─────────────▼──────────────┐  ┌────────▼────────────────────┐
│  监控服务 (FastAPI, :8000)  │  │  投顾服务 (FastAPI, :8001)  │
│  REST 查询 + WebSocket      │  │  /chat + /feedback          │
│  反馈生成器 feedback.py     │──▶│  (orchestrator)             │
└─────────────┬──────────────┘  └────────┬────────────────────┘
              │ HTTP POST 反馈            │ 采集 trace + 注入指令
              └──────────────────────────▼────────────────────┐
                              PostgreSQL (Neon)               │
                     tasks/traces/anomaly_events/            │
                     quality_scores/optimization_suggestions/ │
                     agent_instructions                       │
                              └───────────────────────────────┘
```

- **监控服务**：监控平台后端，负责 REST 查询、WebSocket 推送、反馈生成。
- **投顾服务**：orchestrator，import `demo_advisory`（图）+ `agent_monitor`（适配器/管线），跑投顾链路并采集监控数据。
- **共享数据库**：两个服务共享的唯一资源，也是「数据库即接口」的解耦边界。

## 2. 代码组织

```
agent_monitor/            # Part 1：通用监控平台
├── core/
│   ├── models.py         # TraceRecord 通用数据模型
│   ├── collector.py      # 模块一：执行监控采集
│   ├── anomaly.py        # 模块二：异常检测（三层扫描）
│   ├── quality.py        # 模块三：质量评估（五维度 + LLM-as-Judge）
│   ├── optimizer.py      # 模块四：结果筛选优化
│   ├── pipeline.py       # 端到端管线（四模块串联落库）
│   ├── feedback.py       # 反馈生成器（监控 → 投顾 HTTP 推送）
│   ├── instructions.py   # 动态指令库操作
│   └── llm_client.py     # LLM 客户端（OpenAI 兼容）
├── adapters/
│   ├── base.py           # MonitoringAdapter 抽象接口
│   └── langgraph.py      # LangGraph 适配器（astream_events 驱动）
├── api/                  # FastAPI 后端（13 REST + WebSocket + feedback）
└── db/                   # SQLAlchemy ORM + Alembic 迁移

demo_advisory/            # Part 2：金融投顾 Demo（零侵入，不 import agent_monitor）
├── agents/               # 6 业务 Agent + 记忆 Agent + 公共 _llm
├── graph.py              # LangGraph 链路编排
├── mock_data/            # yfinance 真实 A 股数据（5 只股票）
└── prompts/              # System Prompt 模板

demo_service/             # 投顾服务（orchestrator，import 双方）
├── main.py               # /chat + /feedback + /ws
└── schemas.py            # 请求/响应模型

dashboard/                # Web 前端（React + AntD + AntV G6 + ECharts）
tests/                    # 25 个单元/集成测试
```

## 3. 核心模块设计

### 3.1 通用 Trace 数据模型
`TraceRecord` 是框架无关的标准化数据结构（dataclass），包含：`trace_id / task_id / agent_name / agent_role / parent_trace_id / start_time / end_time / duration_ms / input_prompt / output_content / token_used / status / error_message` 等。适配器层的唯一职责是将框架原生事件转换为 TraceRecord。

### 3.2 适配器层（零侵入关键）
- `MonitoringAdapter` 抽象基类定义 `emit / set_on_trace / get_framework_name`。
- `LangGraphCallback` 通过 `graph.astream_events()` 采集每个节点的执行 Trace：节点名取自 `metadata.langgraph_node`，`task_id` 每次运行生成一次、`trace_id` 用节点 `run_id`，`parent_trace_id` 从图拓扑（`get_graph().edges`）提取。
- 关键点：LangGraph 1.x 的节点事件不再走旧版 `config["callbacks"]`（`serialized=None`），必须用 `astream_events`。

### 3.3 四大监控模块
| 模块 | 职责 | 关键实现 |
|------|------|----------|
| 采集 collector | TraceRecord → PostgreSQL | `save` 写 traces/tasks，`create_task` 预建任务避免并发冲突 |
| 异常 anomaly | 三层扫描 | 执行层（超时/失败）、行为层（循环/缺节点）、输出层（空输出） |
| 质量 quality | 五维度 + LLM-as-Judge | 规则层（compliance/completeness/timeliness）+ LLM 层（accuracy/relevance，`asyncio.gather` 并行） |
| 优化 optimizer | 四步 Pipeline | 异常过滤 → 质量排序 → 多样性去重 → 推荐；双通道建议（human + agent） |

### 3.4 端到端管线（pipeline.py）
`MonitoringPipeline.process_trace()` 串联四模块：采集 → 异常 → 质量 → 建议，全部落库。多条 Trace 用 `asyncio.gather` 并发处理。

### 3.5 反馈闭环
```
chat 跑 demo → 管线写质量分 → demo 调监控 /api/feedback/generate
  → 监控读质量分（<75 维度）+ 高危异常 → 生成反馈指令 → HTTP 推 demo /advisory/feedback
  → demo 写入 agent_instructions（去重覆盖）→ 下次 chat 自动注入 Agent prompt
```
- **触发条件**：合规违规 > 高危异常 > 质量分 < 75（阈值从 70 上调）。
- **动态指令库**：`agent_instructions` 表，按 (target_agent, dimension) 去重覆盖；`status` 状态机（active/superseded/applied/expired）。
- **注入机制**：`demo_advisory` 的 `load_prompt()` 在加载 System Prompt 时拼接活跃指令块，5 个 Agent 的 `load_prompt` 移入 `run()` 实现每次执行动态加载。

### 3.6 记忆 Agent（多轮对话）
`memory_agent.py` 读取对话历史 + 当前提问，用 LLM 补全省略指代（如"那风险大不大？" → "贵州茅台（600519）的风险大不大？"），返回明确查询供下游 Agent 使用。

## 4. 数据模型（6 张表）

| 表 | 说明 | 关键字段 |
|------|------|----------|
| tasks | 一次完整 Agent 链路执行 | task_id（UUID）、status、created_at |
| traces | 每个 Agent 一条执行记录 | trace_id、task_id、agent_name、parent_trace_id、duration_ms、token_used、status、quality_score |
| anomaly_events | 异常事件 | trace_id、task_id、anomaly_type、severity、layer |
| quality_scores | 质量评分 | trace_id、五维度分、overall_score、eval_method |
| optimization_suggestions | 优化建议（双通道） | task_id、trace_id、target、low_dimension、content |
| agent_instructions | 反馈指令库 | target_agent、dimension、instruction、status、priority |

## 5. API 设计

**监控服务（:8000，前缀 `/api`）**
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| GET | /tasks | 任务列表 |
| GET | /tasks/{task_id} | 任务详情 |
| GET | /traces | Trace 列表（可过滤 task_id/agent_name/status） |
| GET | /traces/{trace_id} | Trace 详情 |
| GET | /anomalies | 异常列表（可过滤 severity） |
| GET | /quality/{trace_id} | 质量评分 |
| GET | /suggestions | 优化建议 |
| POST | /feedback/generate | 反馈生成（读取质检结果 → 生成指令 → 推送投顾） |
| WS | /ws | WebSocket 实时推送 |

**投顾服务（:8001，前缀 `/advisory`）**
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| POST | /chat | 跑投顾链路 + 监控，返回报告 + 监控摘要 + 反馈 |
| POST | /feedback | 接收监控推送的反馈指令 |
| WS | /ws | 进度推送（步骤条实时点亮） |

## 6. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 监控与 Demo 解耦 | 零侵入 + 适配器模式 | `demo_advisory` 不 import `agent_monitor`，换场景不动监控代码 |
| 进程架构 | 两个 FastAPI 进程 | 监控服务（8000）+ 投顾服务（8001），HTTP 反馈链路体现"两个系统对话" |
| trace 采集 | 投顾服务直接写共享 DB | 简单，反馈链路已是真 HTTP，trace 不必再叠 HTTP |
| 反馈载体 | HTTP 推送 JSON | 跨服务解耦，演示"监控 → demo 自动闭环" |
| 动态更新 | 指令库 + 运行时注入 | 最小侵入 + 可回溯（状态机 + 去重覆盖） |
| 多轮上下文 | 记忆 Agent（指代解析） | 专职 Agent 展示多智能体协同 |
| 合规防线 | 四层递进 | Prompt → 规则 → 独立合规 Agent → 阻断 |
| LLM 密钥 | AM_LLM_* 与 DEMO_LLM_* 分离 | 监控平台与 Demo 用独立 key |

## 7. 技术栈

| 层级 | 技术 |
|------|------|
| Agent 框架 | LangGraph |
| 后端 | Python + FastAPI + SQLAlchemy(async) + Alembic |
| 前端 | React 18 + TypeScript + Vite + Ant Design + AntV G6 + ECharts |
| 数据库 | PostgreSQL（Neon 免费层） |
| LLM | OpenAI 兼容接口（DeepSeek） |
| 实时通信 | WebSocket |
| CI/CD | GitHub Actions（test + lint + dashboard build） |
