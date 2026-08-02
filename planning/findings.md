# Findings: 跨智能体协同执行智能监控与结果筛选优化研究

## 技术调研

### 股票数据源
- **yfinance**（Yahoo Finance）：A 股支持良好，代码格式 `600519.SS`/`300750.SZ`，需要代理访问。日线 OHLCV + 基本面（PE/PB/ROE）。
- **akshare**：东方财富 API 在国内被墙，同花顺接口能用但仅限财务数据。不适合 Demo。

### Agent 框架
- **LangGraph**：StateGraph + TypedDict 状态管理，并行分支通过多入边实现，State 更新需避免 `**state` 全量替换（会触发并发写冲突），每个 node 只返回自己的新字段。

### 可视化方案
待补充

## 踩坑记录

### ruff 版本不一致导致 CI lint 反复失败
- **现象**：本地 ruff 0.15.22 通过，CI ruff 版本更新，引入了 UP045/UP007/I001/BLE001/DTZ/B008/RUF012 等额外规则
- **根因**：本地 ruff 未升级，CI 每次运行最新版
- **解决**：升级本地 ruff → `ruff check --fix` 自动修复 → pyproject.toml 配置豁免规则（B008: FastAPI 标准模式, BLE001: Demo LLM fallback, DTZ: 测试代码用 naive datetime）
- **教训**：项目初期就应锁定 CI 的 ruff 版本或至少保持本地与 CI 一致

### LangGraph 并行分支 State 冲突
- **现象**：`InvalidUpdateError: At key 'query': Can receive only one value per step`
- **原因**：并行分支的 node 返回 `{**state, "new_field": val}` 时复制了整个旧 state，两个分支同时写同一个 key
- **解决**：每个 node 只返回自己的新字段，LangGraph 自动合并

### Windows + asyncpg + Neon SSL 连接
- **现象**：`ConnectionDoesNotExistError` 或 `unexpected keyword argument 'sslmode'`
- **解决**：async 连接用 `?ssl=require`（非 `?sslmode=require`），sync 保留 `?sslmode=require`。alembic.ini 用 sync URL，env.py 运行时改用 Settings 的 async URL。

## 领域知识

### 多智能体投顾系统特点
- 链式调用：数据采集 → 并行分析 → 风控 → 决策 → 合规
- 6 Agent 分工：采集、技术面、基本面、风控、决策、合规（最后一关）
- 关键设计：监控平台(demo_advisory)零侵入——通过 LangGraph callbacks 从外部采集

## 参考资料
- 设计文档：docs/superpowers/specs/2026-07-10-agent-monitoring-system-design.md
- Demo 脚本：demo_pipeline.py（监控链路的端到端演示）
