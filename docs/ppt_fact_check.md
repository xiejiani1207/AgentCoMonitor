# ppt_fact_check.md

事实审计：区分"有直接证据 / 合理总结 / 必须问我"。

## A — 有直接证据（代码/文档/Git 可直接证明）

| 事实 | 证据 |
|---|---|
| 7 个业务 Agent（含 3 个并行决策） | `demo_advisory/agents/*.py`、`graph.py` |
| 零侵入监控（Demo 不 import 监控） | `agent_monitor/adapters/langgraph.py` |
| 三层异常检测 | `agent_monitor/core/anomaly.py` |
| 五维质量评估 + LLM-as-Judge | `agent_monitor/core/quality.py` |
| 四步结果筛选（异常过滤→排序→去重→推荐） | `agent_monitor/core/optimizer.py` |
| 反馈闭环 + 动态指令库 | `agent_monitor/core/feedback.py`、`instructions.py` |
| 敏感词库 + 句级检测/拦截 | `agent_monitor/core/sensitive_words.py`、迁移 003 |
| 多轮对话 + 记忆 Agent | `demo_advisory/agents/memory_agent.py` |
| 双服务架构 + WebSocket | `demo_service/main.py`、`agent_monitor/api/` |
| 25 个测试 + CI | `tests/`、`.github/workflows/test.yml` |
| 7 张数据库表 | `agent_monitor/db/migrations/` |
| 技术栈 | `pyproject.toml`、`dashboard/package.json` |

## B — 基于实现的合理总结（代码没写这句话，但能归纳）

- "系统能回答：谁在跑、跑得对不对、结果能不能发"
- "不直接相信第一次生成结果"
- "规则约束 + 大模型语义评价结合"
- "证券场景看重可追溯、合规、质量可控"

## C — 必须问我（不要擅自填入 PPT）

- 姓名 / 实习部门 / 岗位 / 时间 / 辅导员 / 学校专业
- 哪些工作是我本人完成、哪些是 AI 辅助（见 my_contribution.md）
- 证券业务场景是否做过真实验证
- 某个 Demo 是否适合公开演示
- 中信建投企业文化具体表述
- 辅导员寄语内容

> 凡 C 类，在 PPT 中一律用 `【待本人确认/填写】` 占位。
