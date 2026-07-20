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
- [x] 通用 Trace 数据模型 + SQLAlchemy ORM（5 张核心表）
- [x] 适配器抽象接口 + LangGraph MonitoringCallback
- [x] 执行监控采集模块（collector）
- [x] 异常检测模块（三层扫描引擎）
- [x] 输出质量评估模块（五维度两层打分 + LLM-as-Judge）
- [x] 结果筛选优化模块（四步 Pipeline + 双通道建议）
- [x] 单元测试 + 集成测试（25 个）
- [x] **门禁: CI 全绿**

### Phase 3: Demo 场景 + API + Dashboard
- [ ] 金融投顾 Agent 链（demo_advisory/）— 数据采集→技术面/基本面分析→风控→决策→合规
- [ ] FastAPI 后端（routes + WebSocket）
- [ ] Web Dashboard 前端（React + AntV G6 + ECharts）

### Phase 4: 文档与交付
- [ ] 需求文档
- [ ] 设计文档（已有一版，需更新）
- [ ] 开发文档
- [ ] 使用说明
- [ ] 演示 PPT
- [ ] **门禁: 文档齐全 + Demo 可演示**

## 关键决策记录

| 决策项 | 决策 | 原因 |
|--------|------|------|
| 领域倾向 | 混合策略（金融投顾 + 通用） | Demo 有金融场景也有通用场景 |
| 仓库策略 | 单仓库（monorepo） | 7 周周期，双仓库维护成本高 |
| 数据库 | Neon 免费层（PostgreSQL） | 免运维，导师 clone 即用 |
| Demo 与监控的关系 | Demo 零侵入（通过 callbacks 注入） | 换 Demo 场景不动监控代码 |
| LLM 集成 | OpenAI 兼容接口（DeepSeek） | 成本低，API 兼容性好 |

## 风险与阻塞项

| 风险 | 影响 | 状态 |
|------|------|------|
| 导师对方向有不同意见 | 设计返工 | 已通过 |
| LLM API 稳定性 | 质量评估不可靠 | 规则层兜底，LLM 失败自动降级 |
