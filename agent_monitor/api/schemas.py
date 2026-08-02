"""Pydantic 请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel

# ---- Task ----

class TaskOut(BaseModel):
    task_id: str
    title: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---- Trace ----

class TraceOut(BaseModel):
    trace_id: str
    task_id: str
    agent_name: str
    agent_role: str | None = None
    parent_trace_id: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: int | None = None
    input_prompt: str | None = None
    output_content: str | None = None
    token_used: int | None = None
    status: str
    error_message: str | None = None
    quality_score: float | None = None

    class Config:
        from_attributes = True


# ---- Anomaly ----

class AnomalyOut(BaseModel):
    id: int
    trace_id: str | None = None
    task_id: str
    anomaly_type: str
    severity: str
    layer: str
    description: str
    suggestion: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Quality ----

class QualityScoreOut(BaseModel):
    trace_id: str
    accuracy: float | None = None
    completeness: float | None = None
    relevance: float | None = None
    compliance: float | None = None
    timeliness: float | None = None
    overall_score: float
    eval_method: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Suggestion ----

class SuggestionOut(BaseModel):
    id: int
    trace_id: str | None = None
    task_id: str
    target: str
    low_dimension: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- WebSocket Events ----

class WsEvent(BaseModel):
    event: str
    data: dict
