"""投顾 demo 服务的请求/响应模型。"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str


class AdvisoryReport(BaseModel):
    stock_code: str | None = None
    stock_name: str | None = None
    technical_report: str = ""
    fundamental_report: str = ""
    risk_report: str = ""
    decision: str = ""
    compliance_result: str = ""
    compliance_score: int | None = None
    final_output: str = ""


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


class ChatResponse(BaseModel):
    query: str
    report: AdvisoryReport
    monitoring: MonitoringSummary


class FeedbackItem(BaseModel):
    target_agent: str
    dimension: str
    instruction: str
    priority: int = 0
