"""模块一：执行监控采集模块。

接收适配器回调的 TraceRecord，持久化到 PostgreSQL，推送到 WebSocket。
"""

import logging
from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_monitor.core.models import TraceRecord
from agent_monitor.db.models import Task as TaskModel
from agent_monitor.db.models import Trace as TraceModel
from agent_monitor.db.session import async_session

logger = logging.getLogger(__name__)

# WebSocket 推送回调类型：接收 trace_id
WebSocketNotifier = Callable[[str], Awaitable[None]]


class TraceCollector:
    """Trace 采集器——将 TraceRecord 写入 PostgreSQL，可选 WebSocket 推送。

    用法:
        collector = TraceCollector(ws_notifier=my_push_fn)
        adapter.set_on_trace(lambda tr: collector.collect(tr))
    """

    def __init__(self, ws_notifier: WebSocketNotifier | None = None):
        self._ws_notifier = ws_notifier

    async def collect(self, trace: TraceRecord) -> None:
        """采集一条 Trace：持久化 + 推送。"""
        trace_id = await self.save(trace)
        if self._ws_notifier:
            try:
                await self._ws_notifier(trace_id)
            except Exception:
                logger.exception("websocket push failed for trace %s", trace_id)

    async def save(self, trace: TraceRecord) -> str:
        """持久化 TraceRecord 到数据库，返回 trace_id。"""
        async with async_session() as session:
            await self._ensure_task_exists(session, trace.task_id)

            orm_trace = TraceModel(
                trace_id=trace.trace_id,
                task_id=trace.task_id,
                agent_name=trace.agent_name,
                agent_role=trace.agent_role,
                parent_trace_id=trace.parent_trace_id,
                start_time=trace.start_time,
                end_time=trace.end_time,
                duration_ms=trace.duration_ms,
                input_prompt=trace.input_prompt,
                output_content=trace.output_content,
                token_used=trace.token_used,
                decision_type=trace.decision_type,
                decision_summary=trace.decision_summary,
                tool_calls=trace.tool_calls,
                status=trace.status,
                error_message=trace.error_message,
            )
            session.add(orm_trace)
            await session.commit()
            logger.info("trace saved: %s (%s)", trace.trace_id, trace.agent_name)
            return trace.trace_id

    async def _ensure_task_exists(self, session: AsyncSession, task_id: str) -> None:
        result = await session.execute(
            select(TaskModel).where(TaskModel.task_id == task_id)
        )
        if result.scalar_one_or_none() is None:
            session.add(TaskModel(task_id=task_id))
