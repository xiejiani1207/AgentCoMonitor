"""投顾 demo 服务——HTTP 入口，跑投顾链路并接入监控。

独立进程（8001），与监控服务（8000）通过共享 DB + 反馈 HTTP 交互。
本服务是 orchestrator：import demo_advisory（图）+ agent_monitor（适配器/管线），
demo_advisory/ 自身仍保持零侵入。

运行: uvicorn demo_service.main:app --port 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent_monitor.adapters.langgraph import LangGraphCallback
from agent_monitor.core.pipeline import MonitoringPipeline
from demo_advisory.graph import build_graph
from demo_service.schemas import (
    AdvisoryReport,
    ChatRequest,
    ChatResponse,
    MonitoringSummary,
    TraceSummary,
)

app = FastAPI(title="投顾 Demo 服务", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="查询不能为空")

    # 跑投顾链路 + 零侵入采集
    collected: list = []
    monitor = LangGraphCallback(on_trace=collected.append)
    graph = build_graph()
    final_state = await monitor.run(graph, {"query": query})

    if not final_state.get("stock_code"):
        raise HTTPException(
            status_code=404,
            detail=final_state.get("error") or "未找到匹配的股票",
        )

    # 逐条 Trace 走监控管线（采集/异常/质量/建议 → 落库）
    pipeline = MonitoringPipeline()
    processed = []
    for trace in collected:
        processed.append(await pipeline.process_trace(trace))
    if collected:
        await pipeline.finalize_task(collected[0].task_id)

    return ChatResponse(
        query=query,
        report=AdvisoryReport(
            stock_code=final_state.get("stock_code"),
            stock_name=final_state.get("stock_name"),
            technical_report=final_state.get("technical_report", ""),
            fundamental_report=final_state.get("fundamental_report", ""),
            risk_report=final_state.get("risk_report", ""),
            decision=final_state.get("decision", ""),
            compliance_result=final_state.get("compliance_result", ""),
            compliance_score=final_state.get("compliance_score"),
            final_output=final_state.get("final_output", ""),
        ),
        monitoring=_build_monitoring(collected, processed),
    )


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
