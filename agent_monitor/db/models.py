import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    Float,
    String,
    Text,
    DateTime,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from agent_monitor.db.session import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.utcnow()


class Task(Base):
    """任务元信息——每次用户发起一次完整的 Agent 链路执行。"""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(UUID(as_uuid=False), unique=True, nullable=False, default=new_uuid)
    title = Column(String(256), nullable=True)
    status = Column(
        Enum("pending", "running", "completed", "failed", name="task_status"),
        default="pending",
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    traces = relationship("Trace", back_populates="task", order_by="Trace.start_time")


class Trace(Base):
    """Agent 执行 Trace 记录——核心表，每次 Agent 执行一条。"""

    __tablename__ = "traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(UUID(as_uuid=False), unique=True, nullable=False, default=new_uuid)
    task_id = Column(UUID(as_uuid=False), ForeignKey("tasks.task_id"), nullable=False)

    agent_name = Column(String(128), nullable=False)
    agent_role = Column(String(256), nullable=True)
    parent_trace_id = Column(UUID(as_uuid=False), nullable=True)

    start_time = Column(DateTime, nullable=False, default=utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    input_prompt = Column(Text, nullable=True)
    output_content = Column(Text, nullable=True)
    token_used = Column(Integer, nullable=True)

    decision_type = Column(String(64), nullable=True)
    decision_summary = Column(Text, nullable=True)
    tool_calls = Column(JSONB, default=list)

    status = Column(
        Enum("pending", "success", "error", "retry", "timeout", name="trace_status"),
        default="pending",
        nullable=False,
    )
    error_message = Column(Text, nullable=True)

    quality_score = Column(Float, nullable=True)
    quality_metrics = Column(JSONB, nullable=True)

    created_at = Column(DateTime, nullable=False, default=utcnow)

    task = relationship("Task", back_populates="traces")

    __table_args__ = (
        Index("idx_traces_task_time", "task_id", "start_time"),
        Index("idx_traces_agent_status", "agent_name", "status"),
        Index("idx_traces_parent", "parent_trace_id"),
    )


class AnomalyEvent(Base):
    """异常事件记录。"""

    __tablename__ = "anomaly_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(UUID(as_uuid=False), ForeignKey("traces.trace_id"), nullable=True)
    task_id = Column(UUID(as_uuid=False), nullable=False)

    anomaly_type = Column(String(64), nullable=False)
    severity = Column(
        Enum("high", "medium", "low", name="anomaly_severity"), nullable=False
    )
    layer = Column(
        Enum("execution", "behavior", "output", name="anomaly_layer"), nullable=False
    )
    description = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        Index("idx_anomalies_severity_time", "severity", "created_at"),
        Index("idx_anomalies_task", "task_id"),
    )


class QualityScore(Base):
    """质量评分记录。"""

    __tablename__ = "quality_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(
        UUID(as_uuid=False), ForeignKey("traces.trace_id"), unique=True, nullable=False
    )

    accuracy = Column(Float, nullable=True)
    completeness = Column(Float, nullable=True)
    relevance = Column(Float, nullable=True)
    compliance = Column(Float, nullable=True)
    timeliness = Column(Float, nullable=True)

    overall_score = Column(Float, nullable=False)
    eval_method = Column(String(32), nullable=True)
    eval_detail = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        Index("idx_quality_trace", "trace_id"),
        Index("idx_quality_score", "overall_score"),
    )


class OptimizationSuggestion(Base):
    """优化建议记录——双通道：人类可读 + Agent 结构化指令。"""

    __tablename__ = "optimization_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(UUID(as_uuid=False), nullable=False)
    trace_id = Column(UUID(as_uuid=False), ForeignKey("traces.trace_id"), nullable=True)

    target = Column(Enum("human", "agent", name="suggestion_target"), nullable=False)
    low_dimension = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    structured_cmd = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
