"""投顾 demo 服务——HTTP 入口，跑投顾链路并接入监控。

独立进程（8001），与监控服务（8000）通过共享 DB + 反馈 HTTP 交互。
本服务是 orchestrator：import demo_advisory（图）+ agent_monitor（适配器/管线），
demo_advisory/ 自身仍保持零侵入。

运行: uvicorn demo_service.main:app --port 8001
"""

import asyncio
import json
import logging
import os

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import update

from agent_monitor.adapters.langgraph import LangGraphCallback
from agent_monitor.core.instructions import get_active_instructions
from agent_monitor.core.pipeline import MonitoringPipeline
from agent_monitor.core.sensitive_words import (
    detect_sensitive_sentences,
    intercept_sentences,
    refresh_sensitive_words,
)
from agent_monitor.db.models import AgentInstruction, AnomalyEvent
from agent_monitor.db.session import async_session
from demo_advisory.agents._llm import set_active_instructions
from demo_advisory.agents.memory_agent import run as resolve_query
from demo_advisory.graph import build_graph
from demo_service.schemas import (
    AdvisoryReport,
    ChatRequest,
    ChatResponse,
    FeedbackItem,
    MonitoringSummary,
    RankedResultOut,
    TraceSummary,
    ViolationItem,
)

logger = logging.getLogger(__name__)

# 监控服务地址（反馈生成器调用）
MONITOR_URL = os.environ.get("MONITOR_URL", "http://localhost:8000")


app = FastAPI(title="投顾 Demo 服务", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """管理 chat 进度 WebSocket 连接，广播 agent_finished 事件。"""

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)

    async def broadcast(self, event: str, data: dict) -> None:
        payload = json.dumps({"event": event, "data": data}, default=str)
        stale: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


manager = ConnectionManager()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/advisory/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/advisory/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="查询不能为空")

    # 多轮对话：记忆 agent 解析省略指代（如「那风险呢」→ 补齐股票代码）
    resolved_query = resolve_query(req.history, query) if req.history else query

    collected: list = []
    broadcast_tasks: list = []

    # 注入监控反馈的活跃优化指令（动态指令库）
    set_active_instructions(await get_active_instructions())
    # 刷新敏感词库缓存（合规检测使用）
    await refresh_sensitive_words()

    def on_trace(trace):
        collected.append(trace)
        # 每个 Agent 结束即广播进度（供前端步骤条实时点亮）
        broadcast_tasks.append(
            asyncio.create_task(
                manager.broadcast(
                    "agent_finished",
                    {
                        "task_id": trace.task_id,
                        "agent_name": trace.agent_name,
                        "status": trace.status,
                    },
                )
            )
        )

    monitor = LangGraphCallback(on_trace=on_trace)
    graph = build_graph()
    final_state = await monitor.run(graph, {"query": resolved_query})

    # 确保进度广播全部发出
    if broadcast_tasks:
        await asyncio.gather(*broadcast_tasks)

    if not final_state.get("stock_code"):
        raise HTTPException(
            status_code=404,
            detail=final_state.get("error") or "未找到匹配的股票",
        )

    # 演示模式：注入合规违规 + 超时异常（透明标注）
    if req.demo_mode:
        inject_issues(collected, final_state)
        logger.info("演示模式：已注入合规违规 + 超时异常")

    # 逐条 Trace 走监控管线（并发处理；先预建 task 避免并发建 task 冲突）
    pipeline = MonitoringPipeline()
    processed = []
    if collected:
        await pipeline.collector.create_task(collected[0].task_id)
        processed = await asyncio.gather(
            *(pipeline.process_trace(trace) for trace in collected)
        )
        await pipeline.finalize_task(collected[0].task_id)

    # 触发监控反馈生成（自动闭环：监控 → 反馈 → 指令库）
    feedback = []
    if collected:
        feedback = await _request_feedback(collected[0].task_id)

    # 句级合规检测 + 拦截（在决策输出上）
    decision = final_state.get("decision", "")
    detection = detect_sensitive_sentences(decision)
    violations = detection["violations"]
    clean_decision = intercept_sentences(decision, violations)

    # 记录拦截（复用 anomaly_events，compliance_violation 类型）
    if violations and collected:
        await _record_interception(collected[0].task_id, violations)

    # 结果筛选优化（排序：异常过滤 → 质量排序 → 去重 → 推荐）
    ranking = pipeline.rank(processed)

    return ChatResponse(
        query=query,
        report=AdvisoryReport(
            stock_code=final_state.get("stock_code"),
            stock_name=final_state.get("stock_name"),
            technical_report=final_state.get("technical_report", ""),
            fundamental_report=final_state.get("fundamental_report", ""),
            risk_report=final_state.get("risk_report", ""),
            decision=decision,
            compliance_result=final_state.get("compliance_result", ""),
            compliance_score=final_state.get("compliance_score"),
            final_output=clean_decision,
            violations=[ViolationItem(**v) for v in violations],
        ),
        monitoring=_build_monitoring(collected, processed),
        demo_mode=req.demo_mode,
        feedback=feedback,
        ranking=[
            RankedResultOut(
                agent_name=r.agent_name,
                quality_score=r.quality_score,
                rank=r.rank,
                recommendation=r.recommendation,
            )
            for r in ranking
        ],
    )


@app.post("/advisory/feedback")
async def receive_feedback(items: list[FeedbackItem]):
    """接收监控推送的反馈指令，写入指令库（同 agent+dimension 去重覆盖）。"""
    saved = 0
    async with async_session() as session:
        for item in items:
            await session.execute(
                update(AgentInstruction)
                .where(
                    AgentInstruction.target_agent == item.target_agent,
                    AgentInstruction.dimension == item.dimension,
                    AgentInstruction.status == "active",
                )
                .values(status="superseded")
            )
            session.add(AgentInstruction(
                target_agent=item.target_agent,
                dimension=item.dimension,
                instruction=item.instruction,
                priority=item.priority,
                status="active",
            ))
            saved += 1
        await session.commit()
    return {"saved": saved}


async def _request_feedback(task_id: str) -> list[FeedbackItem]:
    """调用监控服务的反馈生成器（自动闭环）。返回生成的反馈指令。"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{MONITOR_URL}/api/feedback/generate", json={"task_id": task_id}
            )
            resp.raise_for_status()
            data = resp.json()
            return [FeedbackItem(**item) for item in data.get("generated", [])]
    except Exception as exc:
        logger.warning("触发反馈生成失败（监控服务未启动?）: %s", exc)
        return []


def inject_issues(collected: list, final_state: dict) -> None:
    """演示模式：注入合规违规 + 超时异常，确保反馈闭环稳定触发。"""
    for trace in collected:
        if trace.agent_name == "decision_maker":
            trace.output_content += "\n\n【演示注入】保证收益。稳赚不赔。"
        elif trace.agent_name == "technical_analyst":
            trace.duration_ms = 35000  # 超过默认 30s 超时阈值
    # 同时把违规注入到决策文本，供句级检测/拦截
    decision = final_state.get("decision", "")
    final_state["decision"] = decision + "\n\n【演示注入】保证收益。稳赚不赔。"


async def _record_interception(task_id: str, violations: list[dict]) -> None:
    """把拦截记录写入 anomaly_events（compliance_violation 类型）。"""
    async with async_session() as session:
        for v in violations:
            words = "、".join(v["words"])
            session.add(AnomalyEvent(
                trace_id=None,
                task_id=task_id,
                anomaly_type="compliance_violation",
                severity="high",
                layer="output",
                description=f"已拦截违规语句：'{v['sentence']}'（命中敏感词：{words}）",
                suggestion="请删除或修改违规表述",
            ))
        await session.commit()


def _build_monitoring(collected: list, processed: list) -> MonitoringSummary:
    traces = [
        TraceSummary(
            agent_name=p["trace"].agent_name,
            status=p["trace"].status,
            overall_score=p["quality"].overall_score,
        )
        for p in processed
    ]
    anomaly_count = sum(len(p["anomalies"]) for p in processed)
    suggestion_count = sum(len(p["suggestions"]) for p in processed)
    scores = [p["quality"].overall_score for p in processed]
    compliances = [
        p["quality"].compliance
        for p in processed
        if p["quality"].compliance is not None
    ]
    return MonitoringSummary(
        task_id=collected[0].task_id if collected else "",
        traces=traces,
        anomaly_count=anomaly_count,
        suggestion_count=suggestion_count,
        avg_quality_score=round(sum(scores) / len(scores), 2) if scores else None,
        min_compliance=min(compliances) if compliances else None,
    )
