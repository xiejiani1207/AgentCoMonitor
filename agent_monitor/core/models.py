"""通用 Trace 数据模型——框架无关的标准化数据结构。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class TraceRecord:
    """一次 Agent 执行的完整记录。

    任何 Agent 框架适配器都产出这个格式。适配器层的唯一职责就是
    将框架原生事件转换为 TraceRecord。
    """

    agent_name: str
    agent_role: str
    task_id: str
    input_prompt: str
    output_content: str

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_trace_id: Optional[str] = None

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    token_used: Optional[int] = None

    decision_type: str = ""
    decision_summary: str = ""
    tool_calls: list[dict] = field(default_factory=list)

    status: str = "pending"
    error_message: Optional[str] = None

    quality_score: Optional[float] = None
    quality_metrics: Optional[dict] = None


class TraceStatus:
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
    RETRY = "retry"
    TIMEOUT = "timeout"


class AnomalySeverity:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnomalyLayer:
    EXECUTION = "execution"
    BEHAVIOR = "behavior"
    OUTPUT = "output"


class QualityDimension:
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    COMPLIANCE = "compliance"
    TIMELINESS = "timeliness"

    # 默认权重（投顾场景）
    DEFAULT_WEIGHTS = {
        "compliance": 0.30,
        "accuracy": 0.25,
        "completeness": 0.20,
        "relevance": 0.15,
        "timeliness": 0.10,
    }
