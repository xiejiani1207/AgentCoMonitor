# ppt_metrics.md

项目中可安全使用的量化数据。

| 指标 | 数值 | 证据来源 | 是否建议上 PPT |
|---|---:|---|---|
| 业务 Agent 数量 | 7 | `demo_advisory/agents/`（7 个文件） | ✅ 建议 |
| 候选决策数量 | 3 | `demo_advisory/graph.py` | ✅ 建议 |
| 质量评价维度 | 5 | `core/quality.py` | ✅ 建议 |
| 异常检测层数 | 3 | `core/anomaly.py` | ✅ 建议 |
| 数据库表数量 | 7 | `agent_monitor/db/migrations/` | 可选 |
| 自动化测试数 | 25 | `tests/`（pytest 输出） | ✅ 建议 |
| 敏感词默认数量 | 10 | 迁移 003 | 可选 |
| 单次 Demo 耗时 | ~27s（并行化优化后） | 实测 | 可选（注明是原型） |
| REST API 端点 | 13+ | `api/routes.py` | 可选 |
| 前端页面数 | 5（+1 隐藏） | `dashboard/src/pages/` | 可选 |

## 重要说明
> 当前项目**没有足够严谨的量化实验数据**（如准确率、成功率、Recall 等），因为没有跑正式的评测基准。建议答辩采用**定性描述 + 上述结构指标**，不要编造准确率/性能提升数字。
