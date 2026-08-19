"""反馈指令库操作——读取活跃指令，供 demo 运行时注入 prompt。"""

from sqlalchemy import select

from agent_monitor.db.models import AgentInstruction
from agent_monitor.db.session import async_session


async def get_active_instructions() -> dict[str, list[str]]:
    """返回所有 active 指令，按 target_agent 分组。

    Returns:
        {agent_name: [instruction_text, ...]}，按 priority 降序、created_at 升序。
    """
    async with async_session() as session:
        result = await session.execute(
            select(AgentInstruction)
            .where(AgentInstruction.status == "active")
            .order_by(AgentInstruction.priority.desc(), AgentInstruction.created_at)
        )
        instructions = result.scalars().all()

    grouped: dict[str, list[str]] = {}
    for instr in instructions:
        grouped.setdefault(instr.target_agent, []).append(instr.instruction)
    return grouped
