"""集成测试：TraceCollector 持久化到 PostgreSQL，验证迁移后的 schema 与 ORM 对齐。

依赖真实数据库连接（CI 的 PostgreSQL 服务容器，schema 由 `alembic upgrade head` 建立）。
为避免污染生产 Neon 数据库，当 database_url 指向 neon.tech 时自动跳过。
"""

from datetime import datetime

import pytest
from sqlalchemy import select

from agent_monitor.config import settings
from agent_monitor.core.collector import TraceCollector
from agent_monitor.core.models import TraceRecord, TraceStatus
from agent_monitor.db.models import Trace as TraceModel
from agent_monitor.db.session import async_session

pytestmark = pytest.mark.skipif(
    "neon.tech" in settings.database_url,
    reason="跳过生产 Neon 数据库写入",
)

TASK_ID = "11111111-1111-1111-1111-111111111111"
TRACE_ID = "22222222-2222-2222-2222-222222222222"


async def test_collector_save_roundtrip():
    """TraceRecord 写入数据库后，能通过 ORM 按 trace_id 查询回来。"""
    trace = TraceRecord(
        trace_id=TRACE_ID,
        task_id=TASK_ID,
        agent_name="data_collector",
        agent_role="数据采集员",
        input_prompt="查询 600519",
        output_content="已采集行情数据",
        start_time=datetime(2026, 7, 20, 10, 0, 0),
        end_time=datetime(2026, 7, 20, 10, 0, 2),
        duration_ms=2000,
        token_used=100,
        status=TraceStatus.SUCCESS,
    )

    saved_id = await TraceCollector().save(trace)
    assert saved_id == TRACE_ID

    async with async_session() as session:
        row = (
            await session.execute(
                select(TraceModel).where(TraceModel.trace_id == TRACE_ID)
            )
        ).scalar_one()
        assert row.agent_name == "data_collector"
        assert row.task_id == TASK_ID
        assert row.status == "success"
