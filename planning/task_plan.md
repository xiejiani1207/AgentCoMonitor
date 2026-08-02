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
- [ ] 软件工程文档（需求/设计/开发/使用说明）
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
