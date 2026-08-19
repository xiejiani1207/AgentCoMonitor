"""反馈生成器——监控质检结果 → 反馈指令 → HTTP 推送到投顾服务。"""

import logging

import httpx
from sqlalchemy import select

from agent_monitor.db.models import AnomalyEvent, QualityScore, Trace
from agent_monitor.db.session import async_session

logger = logging.getLogger(__name__)

# 触发阈值：质量维度低于此值生成反馈（grilling 决策：70 → 75）
QUALITY_THRESHOLD = 75

# 投顾服务地址（接收反馈）
DEMO_SERVICE_URL = "http://localhost:8001"

# 反馈指令模板（注入到 Agent 的 System Prompt）
INSTRUCTION_TEMPLATES = {
    "compliance": "严格遵守合规要求，不得承诺收益、使用绝对化表述（如「保证」「稳赚」「无风险」）或暗示保本。",
    "accuracy": "确保输出中的数据和事实准确，所有数字和引用需经过校验，不得编造。",
    "completeness": "输出需包含完整的分析要素，覆盖所有关键检查项，不得遗漏。",
    "relevance": "紧扣用户问题作答，避免跑题或输出无关内容。",
    "timeliness": "确保引用的数据在有效时间窗口内，并标注数据时效。",
    "reliability": "确保执行稳定可靠，避免超时、报错或空输出。",
}

# 维度优先级：合规 > 可靠性(异常) > 其他质量维度
_DIMENSION_PRIORITY = {
    "compliance": 3,
    "reliability": 2,
    "accuracy": 1,
    "completeness": 1,
    "relevance": 1,
    "timeliness": 1,
}

_QUALITY_DIMENSIONS = ["accuracy", "completeness", "relevance", "compliance", "timeliness"]


async def generate_and_push_feedback(task_id: str) -> list[dict]:
    """读取 task 的质检结果，生成反馈指令并 HTTP 推送到投顾服务。"""
    feedback = await _generate(task_id)
    if feedback:
        await _push(feedback)
    return feedback


async def _generate(task_id: str) -> list[dict]:
    feedback: list[dict] = []

    async with async_session() as session:
        # 1. 质量维度低于阈值 → 对应维度指令
        rows = (
            await session.execute(
                select(Trace.agent_name, QualityScore)
                .join(QualityScore, QualityScore.trace_id == Trace.trace_id)
                .where(Trace.task_id == task_id)
            )
        ).all()
        for agent_name, qs in rows:
            for dim in _QUALITY_DIMENSIONS:
                score = getattr(qs, dim)
                if score is not None and score < QUALITY_THRESHOLD:
                    feedback.append({
                        "target_agent": agent_name,
                        "dimension": dim,
                        "instruction": INSTRUCTION_TEMPLATES[dim],
                        "priority": _DIMENSION_PRIORITY[dim],
                    })

        # 2. 高危异常 → 可靠性指令
        anomaly_rows = (
            await session.execute(
                select(Trace.agent_name)
                .join(AnomalyEvent, AnomalyEvent.trace_id == Trace.trace_id)
                .where(Trace.task_id == task_id, AnomalyEvent.severity == "high")
                .distinct()
            )
        ).all()
        for (agent_name,) in anomaly_rows:
            feedback.append({
                "target_agent": agent_name,
                "dimension": "reliability",
                "instruction": INSTRUCTION_TEMPLATES["reliability"],
                "priority": _DIMENSION_PRIORITY["reliability"],
            })

    return feedback


async def _push(feedback: list[dict]) -> None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{DEMO_SERVICE_URL}/advisory/feedback", json=feedback
            )
            resp.raise_for_status()
        logger.info("推送 %d 条反馈指令到投顾服务", len(feedback))
    except Exception as exc:
        logger.warning("推送反馈失败（投顾服务未启动?）: %s", exc)
