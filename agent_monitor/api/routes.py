"""REST API 路由。"""

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from agent_monitor.db.session import get_db
from agent_monitor.db.models import Task, Trace, AnomalyEvent, QualityScore, OptimizationSuggestion
from agent_monitor.api.schemas import (
    TaskOut, TraceOut, AnomalyOut, QualityScoreOut, SuggestionOut,
)
from agent_monitor.api.websocket import ws_manager

router = APIRouter(prefix="/api")


# ---- Tasks ----

@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).order_by(desc(Task.created_at)).offset(offset).limit(limit)
    )
    return result.scalars().all()


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.task_id == task_id))
    return result.scalar_one()


# ---- Traces ----

@router.get("/traces", response_model=list[TraceOut])
async def list_traces(
    task_id: str = Query(None),
    agent_name: str = Query(None),
    status: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Trace).order_by(desc(Trace.start_time))
    if task_id:
        stmt = stmt.where(Trace.task_id == task_id)
    if agent_name:
        stmt = stmt.where(Trace.agent_name == agent_name)
    if status:
        stmt = stmt.where(Trace.status == status)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/traces/{trace_id}", response_model=TraceOut)
async def get_trace(trace_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trace).where(Trace.trace_id == trace_id))
    return result.scalar_one()


# ---- Anomalies ----

@router.get("/anomalies", response_model=list[AnomalyOut])
async def list_anomalies(
    task_id: str = Query(None),
    severity: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AnomalyEvent).order_by(desc(AnomalyEvent.created_at))
    if task_id:
        stmt = stmt.where(AnomalyEvent.task_id == task_id)
    if severity:
        stmt = stmt.where(AnomalyEvent.severity == severity)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# ---- Quality Scores ----

@router.get("/quality/{trace_id}", response_model=QualityScoreOut)
async def get_quality_score(trace_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(QualityScore).where(QualityScore.trace_id == trace_id)
    )
    return result.scalar_one()


# ---- Optimization Suggestions ----

@router.get("/suggestions", response_model=list[SuggestionOut])
async def list_suggestions(
    task_id: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(OptimizationSuggestion).order_by(desc(OptimizationSuggestion.created_at))
    if task_id:
        stmt = stmt.where(OptimizationSuggestion.task_id == task_id)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# ---- WebSocket ----

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # 保持连接，接收客户端消息（心跳等）
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
