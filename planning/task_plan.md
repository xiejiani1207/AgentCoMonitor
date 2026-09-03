# Task Plan: 跨智能体协同执行智能监控与结果筛选优化研究

## 项目概述

构建多 Agent 协同执行过程的智能监控与结果筛选优化原型系统。交付物：原型系统 + 软件工程文档。

## 阶段规划

### Phase 1: 需求分析与设计
- [x] 完成需求澄清与头脑风暴
- [x] 确定系统架构与技术选型
- [x] 编写设计文档
- [x] **门禁: 导师审核通过**

### Phase 2: 核心监控模块开发
- [x] 通用 Trace 数据模型 + SQLAlchemy ORM
- [x] 适配器抽象接口 + LangGraph MonitoringCallback
- [x] 执行监控采集模块（collector）
- [x] 异常检测模块（三层扫描引擎）
- [x] 输出质量评估模块（五维度 + LLM-as-Judge）
- [x] 结果筛选优化模块（四步 Pipeline + 双通道建议）
- [x] LLM 客户端（DeepSeek 集成）
- [x] 25 个测试（CI 全绿）

### Phase 3: Demo 系统 + API 层
- [x] 金融投顾 Demo：6 Agent LangGraph 链路 + 真实股票数据
- [x] FastAPI 后端：13 个 REST 端点 + WebSocket 实时推送
- [ ] Web Dashboard 前端（React + AntV G6 + ECharts）

### Phase 4: 文档与交付
- [x] 软件工程文档（需求/设计/开发/使用说明）
- [ ] 演示 PPT
- [ ] **门禁: 文档齐全 + Demo 全链路可演示**

## 关键决策记录

| 决策项 | 决策 | 原因 |
|--------|------|------|
| 领域倾向 | 混合策略（金融投顾 + 通用） | Demo 有金融场景也有通用场景 |
| 仓库策略 | 单仓库（monorepo） | 7 周周期，双仓库维护成本高 |
| 数据库 | Neon 免费层（PostgreSQL） | 免运维，导师 clone 即用 |
| Demo 与监控 | Demo 零侵入（callbacks 注入） | 换 Demo 场景不动监控代码 |
| LLM 密钥隔离 | AM_LLM_* 和 DEMO_LLM_* 分开 | 监控平台和 Demo 用独立 API key |
| 股票数据 | yfinance（Yahoo Finance） | A 股支持好，60 天日线 + 财务 |

## 风险与阻塞项

| 风险 | 状态 |
|------|------|
| 导师对方向有不同意见 | 已通过 |
| LLM API 稳定性 | 规则层兜底，LLM 失败自动降级 |
| ruff CI 版本不一致 | 已解决：pyproject.toml 配置豁免规则 |

## 性能优化 Backlog

- [x] 并行化 LLM-as-Judge：`evaluate_async` 内 accuracy/relevance 用 `asyncio.gather` 并行；demo_service 里 6 条 trace 用 `asyncio.gather` 并行（`create_task` 预建 task 避免并发唯一约束冲突）。单次 demo 从 ~40s 降到 ~27s（graph 阶段 ~20s 是固有串行成本）。
- [x] 复用 httpx HTTP 连接：`llm_client.py` 的 `llm_chat` 改为模块级 `_client` 单例复用连接，省掉每次 TLS 握手开销。

## 迭代规划（Phase 3 后）

### 想法 1：投顾 demo 前端 Chat 页面（先做，单轮优先）

| 决策项 | 结论 |
|--------|------|
| 定位 | 单轮问答优先，多轮后续迭代 |
| 多轮方案 | 新增「记忆 agent」= 上下文摘要/画像 agent（压缩历史 + 抽取结构化上下文） |
| 前端位置 | 并入现有 dashboard，新增 `/chat` 路由 |
| 输入 | 自由文本 + 示例快捷按钮（chip） |
| 接口形态 | 同步 REST + 步骤条（复用 /ws `trace_updated` 驱动） |
| 展示 | 分段卡片报告 + 底部监控徽章（质量分/合规/异常） |
| 监控接入 | 每次问答走监控管线（采集 → 异常/质量/筛选） |

关键实现前提：步骤条要实时点亮，需把采集从「先跑完 graph 再批量落库」改成「边执行边落库」（每个 Agent 结束即 save + 广播）。

### 想法 2：监控 → demo 反馈闭环（后做）

| 决策项 | 结论 |
|--------|------|
| 动态更新机制 | 动态指令库（反馈 = 一条「目标 Agent + 维度 + 改进指令」，Agent 运行时读取生效指令注入 prompt） |
| 指令库膨胀治理 | 去重覆盖（按 Agent+维度唯一）+ 状态机（active/superseded/applied/expired）+ 数量上限（每 Agent 3~5 条）；生产规模再加 LLM 压缩（复用记忆 agent） |
| 传输机制 | HTTP 推送（投顾服务暴露 `POST /feedback`，监控服务 httpx 调用） |
| 进程架构 | 两个 FastAPI 进程：监控服务 8000 + 投顾服务 8001 |
| trace 采集 | 投顾服务直接写共享 DB（保留「HTTP 推 trace」作为 B 备选方案） |
| 触发条件 | 三类都触发：合规违规 > 高危异常 > 质量分<阈值；阈值从 70 上调到 75 |
| 演示保证 | 阈值 75 + 「演示模式」注入破绽（透明标注，确定性演示反馈闭环） |
| 自动化程度 | 全自动生效 + 人工可查/可撤销（指令库可回溯，人可手动 disable） |

### 组件边界（共享 vs 独立）

| 资源 | 归属 | 说明 |
|------|------|------|
| Neon 数据库 | **共享** | 唯一共享资源：投顾服务写 trace/质量/异常/建议 + 指令库；监控服务读这些 + 写反馈指令 |
| 前端 Dashboard | **共享** | 一个 React app：监控页面 + `/chat` 页面 |
| 监控服务 (8000) | 独立 | agent_monitor/api：REST + WebSocket + 反馈生成 |
| 投顾服务 (8001) | 独立 | 新 FastAPI：`/chat` + `/feedback`（orchestrator，import 双方） |
| demo_advisory/ | 独立（零侵入） | 不 import agent_monitor |
| agent_monitor/ | 独立 | 不 import demo_advisory |
| LLM 密钥 | 独立 | AM_LLM_*（监控 judge）vs DEMO_LLM_*（demo agents） |

### 跨服务交互（HTTP 边界）

- 监控服务 → 投顾服务 `/feedback`：HTTP POST（唯一跨服务调用 = 反馈链路）
- 投顾服务 → 共享 DB：写 trace（不跨服务，直接写库）
- 前端 → 监控服务 `/api/*` + `/ws`：监控页面
- 前端 → 投顾服务 `/chat`：chat 页面（Vite 需新增代理规则）

### 实施顺序

1. 【想法1】投顾服务雏形：`/chat` 端点（跑 demo + 适配器 + 管线，同步返回报告）
2. 【想法1】chat 前端页面（`/chat` 路由 + 输入框 + 示例 chip + 步骤条 + 分段报告 + 监控徽章）
3. 【想法1】采集改「边执行边落库」+ 步骤条实时联动
4. 【想法2】指令库表 + demo 运行时读取注入
5. 【想法2】监控服务反馈生成器 + HTTP 推送 `/feedback`
6. 【想法2】演示模式注入破绽
7. 【迭代】多轮对话 + 记忆 agent

### 可选优化 Backlog（非必需，导师有要求再做）

- [ ] 多轮对话持久化：当前历史存前端 React state，刷新即失。可加 `conversations` 表 + `conversation_id`，前端用 localStorage 记会话 ID，后端按 ID 存取历史。
- [ ] 反馈指令 LLM 生成：当前指令文本是 `feedback.py` 的 `INSTRUCTION_TEMPLATES` 预设模板（触发是智能的，文本是查表）。可改为 LLM 根据具体输出动态生成更具体的指令，代价是更贵、更不可控。

## 迭代规划（Phase 4 后）：合规增强 + 筛选优化显式化

### 敏感词库（可见 + 可增删）
- DB 表 `sensitive_words`（word 唯一、category、created_at）
- CRUD API + Dashboard「敏感词库」页（增删按钮）
- 检测读取用模块级缓存，增删失效；替换 `quality.py` 硬编码 `COMPLIANCE_BLACKLIST`

### 关键词检测（句级）
- 输出按 。！？ 切句，逐句匹配敏感词
- 命中句整句标红 + 标注命中词（作为原因）
- 评分：每命中一句扣 50 分（1 句 = 50 不合格，2+ = 0）

### 句级拦截
- 命中句从最终输出移除
- 复用 `anomaly_events`（新增 `compliance_violation` 类型）记录「已拦截该说法 + 原因」，异常告警页自动展示

### 与 LLM 合规 Agent 并存
- 关键词线：标红 + 句级拦截 + 评分
- LLM 合规 Agent：语义评分（兜底，抓"换说法"的违规）

### 结果筛选优化显式化
- chat 结果加「结果筛选优化」区块：`rank()` 排序（推荐采纳/备选/存档）+ 过滤理由

### 展示
- 标红在决策/合规检测段，最终输出显示拦截后的干净版

### 实施顺序
1. 敏感词库（表 + CRUD + dashboard 页 + 缓存读取）
2. 关键词检测增强（切句 + 返回命中词句 + 每句扣 50 分）
3. 句级拦截（命中句移除 + compliance_violation 记录）
4. 前端标红 + 最终输出干净版
5. chat 加「结果筛选优化」区块
