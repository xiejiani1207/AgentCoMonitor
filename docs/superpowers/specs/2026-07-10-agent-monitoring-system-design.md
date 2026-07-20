# 跨智能体协同执行智能监控与结果筛选优化系统 — 设计文档

## 1. 项目概述

### 1.1 背景

多智能体协同任务已普及（LangGraph、AutoGen、CrewAI 等框架），Agent 分工执行、链式调用、复杂任务拆解执行已成主流范式。但现有系统普遍依赖人工兜底复盘：Agent 执行日志、任务决策、中间结果、异常行为、输出质量均需研发/运营人工 Review 校验。本系统旨在构建一套自动化的智能监控与结果筛选优化平台，从"人盯着 Agent 干活"升级为"系统自动盯着 Agent 干活"。

### 1.2 交付物

- **原型系统**：Web Dashboard + FastAPI 后端 + Agent 执行层
- **软件工程文档**：需求文档、设计文档、开发文档、使用说明

### 1.3 场景策略

混合策略：Demo 以金融投顾场景为主（面向证券公司 stakeholders），保留通用场景扩展能力。监控系统本身领域无关，通过适配器模式对接不同 Agent 框架。

---

## 2. 系统组成：两大部分

本项目的最终产物由两个相对独立的部分组成：

```
┌──────────────────────────────────────────────────────────────────┐
│                        项目交付物                                  │
│                                                                  │
│  ┌───────────────────────────────┐  ┌──────────────────────────┐ │
│  │  Part 1：通用智能监控与        │  │  Part 2：多智能体金融投顾  │ │
│  │  结果筛选优化平台               │  │  Demo 系统               │ │
│  │  （可复用的监控中间件）          │  │  （被监控的业务对象）      │ │
│  │                              │  │                          │ │
│  │  · Web Dashboard (React)      │  │  · LangGraph Agent 链路   │ │
│  │  · FastAPI 后端服务            │  │  · Mock 金融数据层        │ │
│  │  · 四大核心监控模块             │  │  · 6个业务 Agent         │ │
│  │  · 通用 Trace 数据模型          │  │  · 并行 + 串行混合拓扑     │ │
│  │  · 框架适配器层（LangGraph）     │  │                          │ │
│  │  · PostgreSQL 数据存储          │  │                          │ │
│  └──────────────┬────────────────┘  └────────────┬─────────────┘ │
│                 │                                │               │
│                 │  采集 Trace 数据、注入监控钩子    │               │
│                 └────────────────────────────────┘               │
│                              ↑                                   │
│                     LangGraph 适配器                              │
└──────────────────────────────────────────────────────────────────┘
```

**两者的关系：**

- Part 2 是**被监控的对象**——它运行金融投顾任务，产生 Agent 执行数据。
- Part 1 是**监控者**——它通过 LangGraph 适配器采集 Part 2 的执行数据，做异常检测、质量评估、结果筛选优化，并在 Dashboard 上展示。
- Part 1 不依赖 Part 2 的具体业务逻辑——换掉 Part 2（例如换成代码审查 Agent 链、客服 Agent 链），Part 1 依然能正常工作。

---

## 3. Part 1：通用智能监控与结果筛选优化平台

这是本项目的核心交付——一个**框架无关、可复用的多 Agent 监控中间件**。

### 3.1 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                Web Dashboard (React + TypeScript)         │
│                                                          │
│  概览总览 │ 链路追踪(DAG拓扑图) │ 任务详情 │ 异常告警       │
│                                                          │
│  ECharts (统计图表)  +  AntV G6 (链路拓扑图)               │
│  WebSocket 实时推送  +  REST API 历史查询                  │
└──────────────────────┬──────────────────────────────────┘
                       │ WebSocket (实时) + REST (查询)
┌──────────────────────┴──────────────────────────────────┐
│              FastAPI 后端服务 (Python)                      │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 监控采集  │  │ 异常检测  │  │ 质量评估  │  │ 筛选优化  │ │
│  │ 模块     │→ │ 模块     │→ │ 模块     │→ │ 模块     │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│       │              │              │              │      │
│       └──────────────┴──────────────┴──────────────┘      │
│                          │                                │
│                    WebSocket Manager                       │
│                (向 Dashboard 推送实时数据)                  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│           框架适配器层 (Adapter Layer)                      │
│                                                          │
│  ┌─────────────────────────────────────────────┐        │
│  │         通用 Trace 数据模型 (协议/接口)        │        │
│  │  TraceRecord: 与框架无关的标准化数据结构        │        │
│  └─────────────────────────────────────────────┘        │
│                       ↑ 实现                              │
│  ┌─────────────────────────────────────────────┐        │
│  │       LangGraph 适配器 (Demo 实现)             │        │
│  │  通过 Callback/Hook 机制采集 LangGraph 运行时   │        │
│  │  数据，转换为通用 TraceRecord                   │        │
│  └─────────────────────────────────────────────┘        │
│                       ↑ 可扩展                             │
│            (未来可增加 AutoGen 适配器、CrewAI 适配器等)        │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│               PostgreSQL 数据存储                          │
│                                                          │
│  traces │ anomaly_events │ quality_scores │ suggestions  │
│                                                          │
│  索引策略：按 task_id+时间、agent_name+状态、严重级别查询   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 技术栈明细

| 层级 | 技术 | 版本说明 | 选型理由 |
|------|------|----------|----------|
| Agent 框架 | LangGraph | ≥0.2.x | 最主流的多 Agent 编排框架，支持 StateGraph、checkpoint、streaming |
| 后端框架 | FastAPI | ≥0.110 | 高性能异步 Python Web 框架，原生 WebSocket 支持 |
| 前端框架 | React | 18.x | 生态最丰富，AntV G6 和 ECharts 的 React 封装最成熟 |
| 前端语言 | TypeScript | 5.x | 类型安全，适合中型前端项目 |
| 可视化(图表) | ECharts | 5.x | 国产开源，文档中文友好，图表类型全 |
| 可视化(拓扑图) | AntV G6 | 5.x | 阿里出品，专做关系图和 DAG 图，Agent 链路拓扑的最佳选择 |
| 实时通信 | WebSocket | — | FastAPI 原生支持，低延迟推送 Agent 状态变更 |
| 数据库 | PostgreSQL | 16.x | 完整 SQL 能力，JSONB 支持灵活字段，工业级稳定性 |
| ORM | SQLAlchemy | 2.x | Python 最成熟的 ORM，异步支持完善 |
| LLM 调用 | 统一 LLM 接口层 | — | 对接 Claude API / OpenAI API，通过配置切换 |

### 3.3 四大核心模块详细设计

#### 模块一：执行监控模块

**一句话职责**：采集 Agent 运行时的一切状态，生成标准化的 Trace 记录，并通过 WebSocket 实时推送至 Dashboard。

**具体实践**：

1. **Hook 注入机制**（LangGraph 适配器的核心）：
   - 利用 LangGraph 的 `callbacks` 机制，在每个 Agent node 执行前（`on_chain_start`）和执行后（`on_chain_end`）注入监控钩子
   - 钩子采集：节点名称、输入 prompt、输出 content、开始时间、结束时间、token 用量、工具调用记录
   - 异常时（`on_chain_error`）自动采集错误信息并标记 `status = error`

2. **Trace 数据模型**（通用，与框架无关）：

```python
# 这是适配器层定义的抽象数据结构，任何 Agent 框架适配器都产出这个格式
@dataclass
class TraceRecord:
    # 身份标识
    trace_id: str          # UUID，唯一标识一次 Agent 执行
    agent_name: str        # Agent 名称，如 "technical_analyst"
    agent_role: str        # Agent 角色，如 "技术面分析师"
    task_id: str           # 所属任务的 UUID
    parent_trace_id: str | None  # 上游 Agent 的 trace_id，构建链路拓扑

    # 时间信息
    start_time: datetime
    end_time: datetime
    duration_ms: int       # 执行耗时(毫秒)

    # 输入输出
    input_prompt: str      # 该 Agent 接收的输入
    output_content: str    # 该 Agent 产出的输出
    token_used: int        # Token 消耗量

    # 决策信息
    decision_type: str     # 决策类型，如 "tool_call", "analysis", "recommendation"
    decision_summary: str  # 一句话决策摘要
    tool_calls: list[dict] # 工具调用记录 [{"tool_name": ..., "args": ..., "result": ...}]

    # 状态
    status: str            # "success" | "error" | "retry" | "timeout"
    error_message: str | None

    # 质量（由质量评估模块异步填充）
    quality_score: float | None
    quality_metrics: dict | None  # {"accuracy": 85, "completeness": 90, ...}
```

3. **实时推送机制**：
   - 每个 Agent 执行完毕 → 生成 TraceRecord → 写入 PostgreSQL（持久化）→ 通过 WebSocket 推送到 Dashboard（实时展示）
   - Dashboard 收到推送后更新 DAG 拓扑图中对应节点的颜色和状态

4. **链路拓扑构建**：
   - 通过 `parent_trace_id` 字段串联上下游，自动构建出任务执行的 DAG
   - 并行 Agent（技术面 + 基本面）的 `parent_trace_id` 都指向数据采集 Agent，形成分叉结构

#### 模块二：异常检测模块

**一句话职责**：对 Trace 数据做三层异常扫描，发现异常事件并分级告警。

**具体实践**：

**三层扫描架构：**

```
Trace 数据流入
    ↓
Layer 1：执行层检测（规则引擎）
    - Agent 超时、执行失败、反复重试、Token 飙升
    - 纯规则判定，< 1ms 完成
    ↓
Layer 2：行为层检测（链路分析器）
    - 循环调用检测：同一 agent_name + 同一 input_prompt 在短时间内重复出现
    - 关键节点缺失：任务链路中没有出现必须的 Agent（如风控评估被跳过）
    - 工具调用异常：tool_calls 中含有不存在的工具名或参数格式错误
    ↓
Layer 3：输出层检测（内容分析器）
    - 输出 schema 校验：output_content 是否匹配预期格式（JSON Schema 验证）
    - 空输出/过短输出检测：长度阈值判断
    - 幻觉检测：LLM 比对输出中的实体（股票代码、公司名）与输入上下文的一致性
```

**检测器实现方式**：

| 检测器 | 实现方式 | 触发时机 |
|--------|----------|----------|
| 超时检测 | 配置文件中定义各 Agent 的 timeout 阈值，Trace.duration_ms 比对 | 每条 Trace 写入时 |
| 重试检测 | 查询 Redis/内存中同一 task 的重试计数 | Trace status=retry 时 |
| Token 飙升检测 | 滑动窗口统计该 Agent 历史 token 用量的均值和方差，新值 > μ+2σ 告警 | 每条 Trace 写入时 |
| 循环调用检测 | 内存中维护最近 N 条 (agent_name, input_hash) 的 LRU 缓存，hash 碰撞即告警 | 每条 Trace 写入时 |
| 关键节点缺失 | 定义任务模板（必选 Agent 列表），task 完成时检查是否全体到场 | task status=done 时 |
| Schema 校验 | 定义各 Agent 的 output_schema（JSON Schema 格式），用 jsonschema 库校验 | 每条 Trace 写入时 |
| 幻觉检测 | 用 LLM 做实体一致性比对："输出中出现的实体是否都能在输入上下文中找到？" | 仅对关键 Agent 触发 |

**异常分级与推送**：

- **高严重度**（红色告警）：执行失败、幻觉检测阳性、关键节点缺失 → 立即推送 + Dashboard 告警闪烁
- **中严重度**（黄色告警）：超时、Schema 不匹配、Token 飙升 → 推送 + Dashboard 黄色标记
- **低严重度**（提示）：空输出、部分检查点未覆盖 → 仅记录，不主动推送

#### 模块三：输出质量评估模块

**一句话职责**：对每个 Agent 的输出做多维度量化打分，产出质量分数和诊断信息。

**具体实践**：

**五维度评估体系**：

| 评估维度 | 分值范围 | 评估方式 | 具体实现 |
|----------|----------|----------|----------|
| **准确性** | 0-100 | 规则 + LLM-as-Judge | 用 LLM 做事实核查："输入中的事实 X，输出中是否被正确引用？是否有编造？" |
| **完整性** | 0-100 | 检查点清单 | 为每个 Agent 定义必覆盖的检查点，如技术面分析必须包含 MA/MACD/RSI 三个指标 |
| **相关性** | 0-100 | 语义相似度 + LLM | 计算 input 和 output 的 embedding 余弦相似度，偏离过大的扣分 |
| **合规性** | 0-100 | 规则 + 关键词 + LLM | Layer 2 规则扫描（禁止词清单）+ Layer 3 LLM 合规判断 |
| **时效性** | 0-100 | 数据时间戳 | 检查 Agent 引用的数据是否在有效期内（如"近 3 个月财报数据"） |

**评估策略（两层过滤）**：

```
Agent 输出
    ↓
第一层：规则检查（< 50ms，无 LLM 调用）
    - 合规关键词检测（正则匹配 "保证收益" "稳赚不赔" "无风险" 等）
    - 数据时间戳时效性检查
    - 输出长度/格式基本检查
    ↓
    如果第一层发现严重问题 → 直接标记低分，跳过第二层
    ↓
第二层：LLM-as-Judge（~2-5s，调用 LLM）
    - 准确性：实体一致性检查
    - 完整性：检查点覆盖率
    - 相关性：语义一致性
    - 合规性：深度语义合规审查
    ↓
综合得分 = Σ(维度得分 × 维度权重)
```

**权重策略**（Demo 投顾场景）：
- 合规性：30%（金融场景红线）
- 准确性：25%
- 完整性：20%
- 相关性：15%
- 时效性：10%

权重可通过配置文件调整，不同场景可使用不同权重分配。

#### 模块四：结果筛选优化模块

**一句话职责**：基于质量评分做结果筛选排序，生成面向人员和 Agent 的优化建议。

**具体实践**：

**筛选流程（Pipeline 模式）**：

```
Step 1：异常过滤
    - 遍历同一任务的所有执行结果
    - 排除被异常检测标记为 error/retry 的结果
    - 排除合规性评分 < 阈值（如 60 分）的结果

Step 2：质量排序
    - 按综合质量分降序排列
    - 如果质量分相同 → 按耗时升序排列（优先推荐更快的执行）

Step 3：多样性去重
    - 计算相邻结果的文本相似度（sentence-transformers embedding + cosine）
    - 相似度 > 95% 的结果去重，保留得分更高的那个
    - 目的：避免 Top-3 全是"换汤不换药"的重复内容

Step 4：推荐输出
    - Top-1 → "采纳结果"（最佳选择，绿色高亮）
    - Top-2/3 → "备选结果"（供人工参考，黄色标记）
    - 其余 → "存档结果"（可查看但不推荐）
```

**优化建议生成（双通道输出）**：

```
质量评分中的低分维度
    │
    ├──→ 通道1：人类可读建议（推送至 Dashboard）
    │    格式："[Agent名称] 的 [维度名称] 评分为 [X分]，建议：[具体改进措施]"
    │    示例："技术面分析 Agent 的合规性评分为 45 分，建议：
    │           在输出中增加风险提示语句，移除 '必将上涨' 等确定性表述。"
    │
    └──→ 通道2：Agent 优化指令（结构化 JSON，供 Agent self-correction）
         格式：{"agent": "technical_analyst", "low_dimensions": [...], "action": "regenerate"}
         用途：Agent 收到指令后，基于优化建议重新执行任务
```

**建议模板引擎**：
- 为每个质量维度 × 低分原因组合预定义建议模板
- 运行时根据实际低分维度选择模板，填入具体数据
- 模板支持变量替换，如 `{agent_name}`, `{score}`, `{missing_item}`

---

## 4. Part 2：多智能体金融投顾 Demo 系统

这是为了 Demo 准备的**被监控对象**——一个基于 LangGraph 构建的金融投资顾问多 Agent 协作系统。

**关于 Demo 开发量**：6 个 Agent 中，数据采集、技术面分析、基本面分析、综合决策 4 个 Agent 以 Prompt Engineering + LLM 调用为主，单个 Agent 约 50-80 行代码。风控评估和合规判断 Agent 额外包含规则检测逻辑。Mock 数据为静态 JSON。整体 Demo 开发量约 1-1.5 周，显著少于监控平台的开发量（3-4 周）。Demo 的核心价值是为监控平台提供可展示的被监控对象，不做复杂的业务逻辑。

### 4.1 Agent 链路拓扑

```
                            ┌──────────────────┐
                            │  技术面分析 Agent   │
                            │  · MA/MACD/RSI    │
                            │  · 趋势判断        │
                            │  · 支撑/压力位     │
                     ┌─────→│                    │──────┐
                     │      └──────────────────┘      │
                     │                                │
┌──────────────┐    │                                │   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 数据采集      │    │                                ├──→│ 风控评估      │──→│ 综合决策      │──→│ 合规判断      │──→ 最终输出
│ Agent         │────┤                                │   │ Agent         │   │ Agent         │   │ Agent         │
│ · Mock行情    │    │                                │   │ · 仓位检查     │   │ · 综合打分     │   │ · 多层防线     │
│ · Mock基本面  │    │      ┌──────────────────┐      │   │ · 回撤分析     │   │ · 建议生成     │   │ · 合规扫描     │
│ · Mock财报    │    │      │  基本面分析 Agent   │      │   │ · 合规预检     │   │ · 止损/止盈    │   │ · 拦截/放行    │
└──────────────┘    │      │  · PE/PB/ROE      │      │   └──────────────┘   └──────────────┘   └──────────────┘
                     │      │  · 营收增长       │      │
                     └─────→│  · 行业对比       │──────┘
                            └──────────────────┘
```

**链路特点**：
- **并行段**：技术面分析和基本面分析同时执行（不同的分析维度，无依赖关系）
- **串行段**：数据采集 → 并行分析 → 风控 → 综合决策 → 合规 → 输出（有数据依赖关系必须串行）
- **这种"并行 + 串行混合拓扑"正是监控系统的价值所在**——需要追踪并行分支的状态、检测分支耗时差异、发现分支结果矛盾

### 4.2 六个 Agent 的详细职责

| Agent | 角色 | 输入 | 输出 | Mock 数据 |
|-------|------|------|------|-----------|
| **数据采集** | 信息汇聚 | 用户 query（如"分析茅台"） | 股票行情数据 + 财务数据 + 行业信息 | 预置 3-5 只股票的 mock JSON 数据 |
| **技术面分析** | 技术分析师 | 行情数据 | 技术指标分析报告（趋势、支撑位、技术信号） | 基于 mock 数据的计算逻辑 |
| **基本面分析** | 基本面分析师 | 财务数据 + 行业信息 | 估值分析报告（PE/PB 评价、成长性判断） | 基于 mock 数据的计算逻辑 |
| **风控评估** | 风控专员 | 两份分析报告 | 风险评估报告（仓位建议、回撤预警、合规预检） | 风控规则引擎 |
| **综合决策** | 投顾决策官 | 风控报告 + 两份分析报告 | 投资建议（买入/持有/卖出 + 理由 + 风险提示） | LLM 综合推理 |
| **合规判断** | 合规审查官 | 投资建议文本 | 合规评分 + 放行/拦截/修改建议 | 独立 LLM + 规则引擎 |

### 4.3 Mock 数据层

Demo 不连接真实行情 API，预置 3-5 只股票的完整 Mock 数据：

```python
# 示例：贵州茅台 mock 数据片段
MOCK_STOCKS = {
    "600519": {
        "name": "贵州茅台",
        "industry": "白酒",
        "price": {
            "current": 1680.50,
            "ma_5": 1672.30, "ma_20": 1658.90, "ma_60": 1620.45,
            "macd": {"dif": 12.3, "dea": 8.7, "histogram": 3.6},
            "rsi_14": 58.2,
            "support": 1600.0, "resistance": 1750.0
        },
        "fundamentals": {
            "pe_ttm": 28.5, "pb": 9.2, "roe": 32.1,
            "revenue_growth": 0.18, "profit_growth": 0.15,
            "industry_avg_pe": 32.0, "industry_avg_pb": 8.5
        }
    },
    # ... 更多股票
}
```

每个股票的数据覆盖技术指标所需字段（均线、MACD、RSI、支撑阻力位）和基本面字段（PE、PB、ROE、增长率、行业均值）。

### 4.4 LangGraph 实现要点

```python
# 概念性示例：LangGraph StateGraph 构建
from langgraph.graph import StateGraph, END

class AdvisoryState(TypedDict):
    query: str
    stock_code: str
    market_data: dict | None
    technical_report: str | None
    fundamental_report: str | None
    risk_report: str | None
    decision: str | None
    compliance_result: dict | None
    final_output: str | None

def build_advisory_graph() -> StateGraph:
    graph = StateGraph(AdvisoryState)

    graph.add_node("data_collector", data_collector_node)
    graph.add_node("technical_analyst", technical_analyst_node)
    graph.add_node("fundamental_analyst", fundamental_analyst_node)
    graph.add_node("risk_assessor", risk_assessor_node)
    graph.add_node("decision_maker", decision_maker_node)
    graph.add_node("compliance_checker", compliance_checker_node)

    graph.set_entry_point("data_collector")
    graph.add_edge("data_collector", "technical_analyst")
    graph.add_edge("data_collector", "fundamental_analyst")  # 并行分叉
    graph.add_edge("technical_analyst", "risk_assessor")
    graph.add_edge("fundamental_analyst", "risk_assessor")   # 并行汇合
    graph.add_edge("risk_assessor", "decision_maker")
    graph.add_edge("decision_maker", "compliance_checker")
    graph.add_edge("compliance_checker", END)

    return graph.compile()
```

**监控接入方式**：通过 LangGraph 的 `config["callbacks"]` 参数注入监控钩子：

```python
# 监控平台提供的 LangGraph 适配器
from agent_monitor.adapters.langgraph import MonitoringCallback

monitor = MonitoringCallback(db_session=db, ws_manager=ws_manager)

# 运行 Agent 链时注入监控
result = graph.invoke(
    {"query": "分析茅台"},
    config={"callbacks": [monitor]}  # ← 监控钩子在此注入
)
```

`MonitoringCallback` 会在每个 node 执行时自动采集 Trace 数据，写入 PostgreSQL，并推送到 Dashboard。

---

## 5. 数据流全景图

以下是用户发起一次投顾任务 → Dashboard 展示结果的完整数据流：

```
用户点 Dashboard "发起分析（茅台600519）"
    │
    ▼
│ 1 │ FastAPI 收到请求，创建 task 记录 → INSERT INTO tasks
    │   → 调用 LangGraph 执行 Agent 链路（注入 MonitoringCallback）
    │
    ▼
│ 2 │ 数据采集 Agent 执行
    │   → Callback.on_chain_start()  采集开始时间
    │   → Callback.on_chain_end()    采集输出、耗时、token
    │   → 生成 TraceRecord
    │   → INSERT INTO traces
    │   → WebSocket push → Dashboard 更新 DAG 图节点变绿
    │
    ▼
│ 3 │ 技术面分析 + 基本面分析 并行执行
    │   → 两条 Trace 同时写入（parent_trace_id 指向数据采集的 trace_id）
    │   → Dashboard DAG 图展示并行分叉 + 实时渲染两条分支
    │
    ▼
│ 4 │ 风控评估 → 综合决策 → 合规判断 串行执行
    │   → 每个节点完成时：
    │       a. Trace 写入 PostgreSQL
    │       b. 异常检测模块扫描 Trace（执行层 + 行为层 + 输出层）
    │       c. 质量评估模块打分（规则层 + LLM-as-Judge）
    │       d. 异常事件/质量评分写入数据库
    │       e. WebSocket 推送至 Dashboard
    │
    ▼
│ 5 │ 任务完成
    │   → 结果筛选优化模块运行：异常过滤 → 质量排序 → 去重 → 推荐 Top-3
    │   → 生成优化建议（人类可读 + Agent 结构化指令）
    │   → Dashboard 展示完整任务链路 + 质量评分 + 推荐结果 + 优化建议
```

---

## 6. 合规防线详细设计（多层）

金融投顾场景的法规合规是底线。本系统设计了四层防线，层层递进，跨 Part 1 和 Part 2 协同工作：

```
Layer 1（Prompt 层）→ 属于 Part 2（Demo）
    ↓  各投顾 Agent 的 System Prompt 中注入合规约束
    ↓  作用：预防不合规输出产生
    ↓  局限：LLM 可能被长上下文冲淡约束、被对抗性输入绕过
    ↓
Layer 2（规则层）→ 属于 Part 1（监控平台），异常检测模块的输出层检测
    ↓  关键词黑名单："保证收益""稳赚""无风险""必然""绝对"
    ↓  正则检测：缺少风险提示、缺少"仅供参考"声明
    ↓  作用：拦截明显违规（< 50ms，无 LLM 调用）
    ↓
Layer 3（模型层）→ 属于 Part 2（Demo），链路中的独立合规判断 Agent
    ↓  独立 System Prompt，只做合规判断一件事
    ↓  与被检查 Agent 完全隔离（不同的 LLM 调用上下文）
    ↓  输出：合规评分 + 违规条款编号 + 修改建议
    ↓
Layer 4（阻断层）→ 属于 Part 1（监控平台），质量评估模块的阻断逻辑
    ↓  合规评分 < 40 → 自动拦截，标记"需人工审核"，不展示给用户
    ↓  合规评分 40-70 → 标记"有风险"，展示时附带红色警告标识
    ↓  合规评分 > 70 → 放行，正常展示
```

**各层归属总结**：

| 防线层 | 归属 | 实现位置 |
|--------|------|----------|
| Layer 1：Prompt 约束 | Part 2（Demo） | 投顾 Agent 的 System Prompt |
| Layer 2：规则扫描 | Part 1（监控平台） | 异常检测模块——输出层检测 |
| Layer 3：独立合规 Agent | Part 2（Demo） | Agent 链路末端节点 |
| Layer 4：高风险阻断 | Part 1（监控平台） | 质量评估模块——阻断逻辑 |

**合规判断 Agent（Layer 3）与风控评估 Agent 的关系重申**：

| | 风控评估 Agent | 合规判断 Agent |
|------|------|------|
| 回答的核心问题 | 这个投资方案风险大吗？ | 这个输出能对外说吗？ |
| 关注内容 | 持仓集中度、回撤风险、市场风险敞口 | 是否有"承诺收益"、是否缺风险提示、有无误导表述 |
| 输入来源 | 技术面分析报告 + 基本面分析报告 | 综合决策 Agent 的输出文本 |
| 在链路中的位置 | 决策**前**——影响投资建议的内容 | 决策**后**——输出前的最后一道闸门 |
| 性质 | **业务逻辑**（金融专业判断） | **法规红线**（监管合规审查） |
| 评估结果影响 | 调整投资策略的风险等级或仓位建议 | 决定输出能否发布（放行/修改/拦截） |

---

## 7. Web Dashboard 详细设计

### 7.1 页面结构

| 页面 | URL | 核心功能 | 关键组件 |
|------|-----|----------|----------|
| **概览总览** | `/` | 系统健康度大盘、今日任务数、异常趋势图、最近告警列表 | ECharts 折线图 + 统计卡片 |
| **链路追踪** | `/topology` | 实时 Agent DAG 拓扑图，节点颜色反映状态（运行中=蓝色动效、成功=绿色、失败=红色、告警=黄色闪烁），点击节点展开详情 | AntV G6 DAG 图 |
| **任务详情** | `/task/:id` | 单个任务的完整时间线、每个 Agent 的输入/输出对比、质量评分雷达图、优化建议面板 | ECharts 雷达图 + 时间线 + 折叠面板 |
| **异常告警** | `/alerts` | 异常事件列表（支持按严重级别/Agent/时间筛选）、事件详情展开、处理建议 | Ant Design Table + 筛选栏 |

### 7.2 实时通信协议

**WebSocket 通道** (`ws://host:8000/ws`):

服务端推送事件类型：

```json
{"event": "trace_updated", "data": {"trace_id": "...", "agent_name": "...", "status": "success", "duration_ms": 1234}}
{"event": "anomaly_detected", "data": {"anomaly_id": "...", "type": "timeout", "severity": "high"}}
{"event": "quality_scored", "data": {"trace_id": "...", "score": 87.5, "metrics": {...}}}
{"event": "task_completed", "data": {"task_id": "...", "top_recommendation": {...}}}
```

**REST API 端点**（历史查询）：

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/tasks` | 任务列表（分页） |
| GET | `/api/tasks/:id` | 任务详情 + 完整 Trace 链路 |
| GET | `/api/traces?task_id=&agent_name=&status=` | Trace 查询（支持筛选） |
| GET | `/api/anomalies?severity=&type=&time_range=` | 异常事件查询 |
| GET | `/api/quality/:trace_id` | 单条 Trace 的质量评分详情 |
| POST | `/api/tasks` | 创建新任务（触发 Agent 链路执行） |

---

## 8. 数据库设计（PostgreSQL）

### 8.1 核心表结构

**traces 表**（核心——每次 Agent 执行一条记录）：

```sql
CREATE TABLE traces (
    id              BIGSERIAL PRIMARY KEY,
    trace_id        UUID NOT NULL UNIQUE,
    task_id         UUID NOT NULL REFERENCES tasks(task_id),
    agent_name      VARCHAR(128) NOT NULL,
    agent_role      VARCHAR(256),
    parent_trace_id UUID,              -- 上游 Agent 的 trace_id

    start_time      TIMESTAMPTZ NOT NULL,
    end_time        TIMESTAMPTZ,
    duration_ms     INTEGER,

    input_prompt    TEXT,
    output_content  TEXT,
    token_used      INTEGER,

    decision_type   VARCHAR(64),
    decision_summary TEXT,
    tool_calls      JSONB DEFAULT '[]',

    status          VARCHAR(32) NOT NULL DEFAULT 'pending',
    error_message   TEXT,

    quality_score   FLOAT,
    quality_metrics JSONB,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_traces_task_time ON traces(task_id, start_time DESC);
CREATE INDEX idx_traces_agent_status ON traces(agent_name, status);
CREATE INDEX idx_traces_parent ON traces(parent_trace_id);
```

**anomaly_events 表**：

```sql
CREATE TABLE anomaly_events (
    id              BIGSERIAL PRIMARY KEY,
    trace_id        UUID REFERENCES traces(trace_id),
    task_id         UUID NOT NULL,
    anomaly_type    VARCHAR(64) NOT NULL,   -- timeout / error / retry_loop / hallucination / ...
    severity        VARCHAR(16) NOT NULL,   -- high / medium / low
    layer           VARCHAR(32) NOT NULL,   -- execution / behavior / output
    description     TEXT NOT NULL,
    suggestion      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_anomalies_severity_time ON anomaly_events(severity, created_at DESC);
CREATE INDEX idx_anomalies_task ON anomaly_events(task_id);
```

**quality_scores 表**：

```sql
CREATE TABLE quality_scores (
    id              BIGSERIAL PRIMARY KEY,
    trace_id        UUID NOT NULL REFERENCES traces(trace_id),
    accuracy        FLOAT,    -- 准确性
    completeness    FLOAT,    -- 完整性
    relevance       FLOAT,    -- 相关性
    compliance      FLOAT,    -- 合规性
    timeliness      FLOAT,    -- 时效性
    overall_score   FLOAT NOT NULL,   -- 加权综合分
    eval_method     VARCHAR(32),       -- rule / llm_judge / hybrid
    eval_detail     JSONB,             -- 评估详情
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_quality_trace ON quality_scores(trace_id);
CREATE INDEX idx_quality_score ON quality_scores(overall_score DESC);
```

**optimization_suggestions 表**：

```sql
CREATE TABLE optimization_suggestions (
    id              BIGSERIAL PRIMARY KEY,
    task_id         UUID NOT NULL,
    trace_id        UUID,
    target          VARCHAR(32) NOT NULL,  -- human / agent
    low_dimension   VARCHAR(32) NOT NULL,  -- accuracy / completeness / ...
    content         TEXT NOT NULL,          -- 建议内容
    structured_cmd  JSONB,                 -- 发给 Agent 的结构化优化指令
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 9. 项目目录结构规划

```
AgentCoMonitor/
├── agent_monitor/              # Part 1：通用监控平台（Python 包）
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py           # TraceRecord 等通用数据模型
│   │   ├── collector.py        # 监控采集模块
│   │   ├── anomaly.py          # 异常检测模块
│   │   ├── quality.py          # 质量评估模块
│   │   └── optimizer.py        # 结果筛选优化模块
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py             # 适配器抽象基类
│   │   └── langgraph.py        # LangGraph 适配器实现
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # FastAPI 路由
│   │   ├── websocket.py        # WebSocket 管理
│   │   └── schemas.py          # Pydantic 请求/响应模型
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy ORM 模型
│   │   ├── session.py          # 数据库会话管理
│   │   └── migrations/         # Alembic 迁移文件
│   └── config.py               # 配置管理
│
├── demo_advisory/              # Part 2：金融投顾 Demo 系统
│   ├── __init__.py
│   ├── graph.py                # LangGraph StateGraph 构建
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── data_collector.py
│   │   ├── technical_analyst.py
│   │   ├── fundamental_analyst.py
│   │   ├── risk_assessor.py
│   │   ├── decision_maker.py
│   │   └── compliance_checker.py
│   ├── mock_data/
│   │   ├── __init__.py
│   │   └── stocks.py           # Mock 股票数据
│   └── prompts/                # 各 Agent 的 System Prompt 模板
│       ├── technical_analyst.md
│       ├── fundamental_analyst.md
│       ├── risk_assessor.md
│       ├── decision_maker.md
│       └── compliance_checker.md
│
├── dashboard/                  # Web Dashboard（React + TypeScript）
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Overview.tsx    # 概览总览
│   │   │   ├── Topology.tsx    # 链路追踪（AntV G6）
│   │   │   ├── TaskDetail.tsx  # 任务详情
│   │   │   └── Alerts.tsx      # 异常告警
│   │   ├── components/
│   │   │   ├── AgentDag.tsx    # Agent DAG 图组件
│   │   │   ├── TraceTimeline.tsx
│   │   │   ├── QualityRadar.tsx
│   │   │   └── AlertBadge.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts # WebSocket 连接 hook
│   │   └── App.tsx
│   └── package.json
│
├── docs/                       # 文档
│   ├── superpowers/specs/      # 设计文档
│   ├── requirements.md         # 需求文档
│   ├── development.md          # 开发文档（部署、配置）
│   └── user-guide.md           # 使用说明
│
├── planning/                   # 项目规划文件
│   ├── task_plan.md
│   ├── findings.md
│   └── progress.md
│
├── main.py                     # 启动入口
├── pyproject.toml
├── docker-compose.yml          # PostgreSQL + App 容器编排
└── README.md
```

---

## 10. 开发阶段规划（7 周）

| 阶段 | 内容 | 产出物 | 验收标准 |
|------|------|--------|----------|
| **Phase 1**（第1周） | 需求分析 + 设计 + 环境搭建 | 设计文档定稿、PostgreSQL 就绪、项目骨架 | 导师审核设计文档通过 |
| **Phase 2**（第2-3周） | Part 1 监控模块（采集 + 异常检测 + 质量评估 + 筛选优化） | 四大模块可独立运行，API 可调通 | 单元测试通过，能对 mock Trace 做检测和打分 |
| **Phase 3**（第4周） | Part 2 投顾 Demo + 适配器联调 | 6个 Agent 的 LangGraph 链路可运行，适配器可采集数据 | 投顾链路跑通，监控平台能采到数据 |
| **Phase 4**（第5-6周） | Dashboard 前端开发 | 4 个页面完整实现，WebSocket 实时推送联调 | Dashboard 能实时展示 Agent 链路和告警 |
| **Phase 5**（第7周） | 文档编写 + PPT + 整体联调 | 需求文档、设计文档、开发文档、使用说明、演示 PPT | 全链路演示无故障 |

---

## 11. 待定/后续细化项

以下内容将在开发过程中根据实际运行数据进行细化：

- Trace 数据模型字段（当前为 V1，开发中可能增加扩展字段）
- 异常检测阈值（超时阈值、Token 飙升的 σ 倍数、循环调用窗口大小）
- 质量评估权重（投顾场景默认值已定义，实际运行时可根据专家反馈调参）
- 优化建议模板库（随测试过程中发现的新低分模式持续扩充）
- 合规关键词黑名单（需与金融合规专家确认完整清单）
