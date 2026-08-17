"""端到端监控管线——串联采集、异常、质量、筛选四模块并落库。

每条 Trace 依次流经：采集（traces/tasks）→ 异常检测（anomaly_events）
→ 质量评估（quality_scores）→ 优化建议（optimization_suggestions）。
"""

import logging

from agent_monitor.core.anomaly import AnomalyDetector
from agent_monitor.core.collector import TraceCollector
from agent_monitor.core.models import TraceRecord
from agent_monitor.core.optimizer import ResultOptimizer
from agent_monitor.core.quality import QualityAssessor
from agent_monitor.db.models import (
    AnomalyEvent,
    OptimizationSuggestion,
    QualityScore,
)
from agent_monitor.db.session import async_session

logger = logging.getLogger(__name__)


class MonitoringPipeline:
    """四模块串联管线。

    用法:
        pipeline = MonitoringPipeline()
        await pipeline.process_trace(trace)   # 单条 Trace 全流程落库
        ranked = pipeline.rank(processed)      # 任务级筛选排序
    """

    def __init__(
        self,
        collector: TraceCollector | None = None,
        anomaly_detector: AnomalyDetector | None = None,
        quality_assessor: QualityAssessor | None = None,
        optimizer: ResultOptimizer | None = None,
    ):
        self.collector = collector or TraceCollector()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.quality_assessor = quality_assessor or QualityAssessor()
        self.optimizer = optimizer or ResultOptimizer()

    async def process_trace(self, trace: TraceRecord) -> dict:
        """处理单条 Trace：采集 → 异常 → 质量 → 建议，全部落库。

        Returns:
            处理结果摘要（含 trace、异常、质量、建议），供任务级筛选排序使用。
        """
        # 1. 采集：写入 traces / tasks 表
        await self.collector.save(trace)

        # 2. 异常检测：三层扫描，写入 anomaly_events 表
        anomalies = self.anomaly_detector.detect(trace)
        await self._save_anomalies(anomalies, trace)

        # 3. 质量评估：规则 + LLM-as-Judge，写入 quality_scores 表
        quality = await self.quality_assessor.evaluate_async(trace)
        await self._save_quality(quality)

        # 4. 优化建议：低分维度双通道建议，写入 optimization_suggestions 表
        metrics = {
            k: v
            for k, v in {
                "accuracy": quality.accuracy,
                "completeness": quality.completeness,
                "relevance": quality.relevance,
                "compliance": quality.compliance,
                "timeliness": quality.timeliness,
            }.items()
            if v is not None
        }
        suggestions = self.optimizer.generate_suggestions(trace.trace_id, metrics)
        await self._save_suggestions(suggestions, trace)

        return {
            "trace": trace,
            "anomalies": anomalies,
            "quality": quality,
            "suggestions": suggestions,
        }

    async def finalize_task(self, task_id: str, status: str = "completed") -> None:
        """任务处理完毕后更新状态。"""
        await self.collector.update_task_status(task_id, status)

    def rank(self, processed: list[dict]) -> list:
        """任务级筛选排序——在所有 Trace 处理后调用。"""
        results = [
            {
                "trace_id": p["trace"].trace_id,
                "agent_name": p["trace"].agent_name,
                "output_content": p["trace"].output_content,
                "quality_score": p["quality"].overall_score,
                "anomaly_count": len(p["anomalies"]),
            }
            for p in processed
        ]
        return self.optimizer.rank(results)

    # ---- 落库辅助 ----

    async def _save_anomalies(self, anomalies, trace: TraceRecord) -> None:
        if not anomalies:
            return
        async with async_session() as session:
            for a in anomalies:
                session.add(AnomalyEvent(
                    trace_id=a.trace_id or trace.trace_id,
                    task_id=a.task_id or trace.task_id,
                    anomaly_type=a.anomaly_type,
                    severity=a.severity,
                    layer=a.layer,
                    description=a.description,
                    suggestion=a.suggestion or None,
                ))
            await session.commit()

    async def _save_quality(self, quality) -> None:
        async with async_session() as session:
            session.add(QualityScore(
                trace_id=quality.trace_id,
                accuracy=quality.accuracy,
                completeness=quality.completeness,
                relevance=quality.relevance,
                compliance=quality.compliance,
                timeliness=quality.timeliness,
                overall_score=quality.overall_score,
                eval_method=quality.eval_method,
                eval_detail=quality.eval_detail or None,
            ))
            await session.commit()

    async def _save_suggestions(self, suggestions, trace: TraceRecord) -> None:
        if not suggestions:
            return
        async with async_session() as session:
            for s in suggestions:
                session.add(OptimizationSuggestion(
                    task_id=trace.task_id,
                    trace_id=s.trace_id,
                    target=s.target,
                    low_dimension=s.dimension,
                    content=s.content,
                    structured_cmd=s.structured_cmd,
                ))
            await session.commit()
