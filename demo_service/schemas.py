"""投顾 demo 服务的请求/响应模型。"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    demo_mode: bool = False
    history: list[str] = []


class ViolationItem(BaseModel):
    sentence: str
    words: list[str]


class AdvisoryReport(BaseModel):
    stock_code: str | None = None
    stock_name: str | None = None
    technical_report: str = ""
    fundamental_report: str = ""
    risk_report: str = ""
    decision: str = ""
    compliance_result: str = ""
    compliance_score: float | None = None
    final_output: str = ""
    violations: list[ViolationItem] = []


class TraceSummary(BaseModel):
    agent_name: str
    status: str
    overall_score: float | None = None


class MonitoringSummary(BaseModel):
    task_id: str
    traces: list[TraceSummary]
    anomaly_count: int = 0
    suggestion_count: int = 0
    avg_quality_score: float | None = None
    min_compliance: float | None = None


class FeedbackItem(BaseModel):
    target_agent: str
    dimension: str
    instruction: str
    priority: int = 0


class RankedResultOut(BaseModel):
    agent_name: str
    quality_score: float
    rank: int
    recommendation: str


class ChatResponse(BaseModel):
    query: str
    report: AdvisoryReport
    monitoring: MonitoringSummary
    demo_mode: bool = False
    feedback: list[FeedbackItem] = []
    ranking: list[RankedResultOut] = []
