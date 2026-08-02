"""Pydantic 请求/响应模型。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ---- Task ----

class TaskOut(BaseModel):
    task_id: str
    title: Optional[str] = None
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
    agent_role: Optional[str] = None
    parent_trace_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_prompt: Optional[str] = None
    output_content: Optional[str] = None
    token_used: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    quality_score: Optional[float] = None

    class Config:
        from_attributes = True


# ---- Anomaly ----

class AnomalyOut(BaseModel):
    id: int
    trace_id: Optional[str] = None
    task_id: str
    anomaly_type: str
    severity: str
    layer: str
    description: str
    suggestion: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Quality ----

class QualityScoreOut(BaseModel):
    trace_id: str
    accuracy: Optional[float] = None
    completeness: Optional[float] = None
    relevance: Optional[float] = None
    compliance: Optional[float] = None
    timeliness: Optional[float] = None
    overall_score: float
    eval_method: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Suggestion ----

class SuggestionOut(BaseModel):
    id: int
    trace_id: Optional[str] = None
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
