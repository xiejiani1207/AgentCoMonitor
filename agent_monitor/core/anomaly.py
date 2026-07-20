"""模块二：异常检测模块——三层扫描引擎。

执行层（规则引擎）→ 行为层（链路分析器）→ 输出层（内容分析器）
"""

from dataclasses import dataclass
from typing import Optional
import hashlib

from agent_monitor.core.models import TraceRecord, TraceStatus, AnomalySeverity, AnomalyLayer


@dataclass
class AnomalyResult:
    """检测到的异常（轻量级，非 ORM）。"""
    anomaly_type: str
    severity: str          # high / medium / low
    layer: str             # execution / behavior / output
    description: str
    suggestion: str = ""
    trace_id: Optional[str] = None
    task_id: Optional[str] = None


class AnomalyDetector:
    """三层异常扫描引擎。

    用法:
        detector = AnomalyDetector(timeout_ms=30000, max_retries=3)
        results = detector.detect(trace)
    """

    def __init__(
        self,
        timeout_ms: int = 30_000,
        max_retries: int = 3,
        token_spike_sigma: float = 2.0,
    ):
        self.timeout_ms = timeout_ms
        self.max_retries = max_retries
        self.token_spike_sigma = token_spike_sigma
        # 追踪最近调用的哈希值，用于循环检测
        self._recent_calls: list[str] = []

    def detect(self, trace: TraceRecord) -> list[AnomalyResult]:
        """执行三层检测，返回所有发现的异常。"""
        results: list[AnomalyResult] = []
        results.extend(self._scan_execution(trace))
        results.extend(self._scan_behavior(trace))
        results.extend(self._scan_output(trace))
        return results

    # ---- Layer 1: 执行层检测（规则引擎）----

    def _scan_execution(self, trace: TraceRecord) -> list[AnomalyResult]:
        results: list[AnomalyResult] = []

        if trace.status == TraceStatus.ERROR:
            results.append(AnomalyResult(
                anomaly_type="execution_error",
                severity=AnomalySeverity.HIGH,
                layer=AnomalyLayer.EXECUTION,
                description=f"Agent '{trace.agent_name}' 执行失败: {trace.error_message or '未知错误'}",
                suggestion="检查 Agent 配置和输入数据",
                trace_id=trace.trace_id,
                task_id=trace.task_id,
            ))

        if trace.status == TraceStatus.TIMEOUT or (
            trace.duration_ms is not None and trace.duration_ms > self.timeout_ms
        ):
            results.append(AnomalyResult(
                anomaly_type="timeout",
                severity=AnomalySeverity.HIGH,
                layer=AnomalyLayer.EXECUTION,
                description=f"Agent '{trace.agent_name}' 超时 ({trace.duration_ms}ms > {self.timeout_ms}ms)",
                suggestion="增加超时阈值或优化 Agent 逻辑",
                trace_id=trace.trace_id,
                task_id=trace.task_id,
            ))

        return results

    # ---- Layer 2: 行为层检测（链路分析器）----

    def _scan_behavior(self, trace: TraceRecord) -> list[AnomalyResult]:
        results: list[AnomalyResult] = []

        call_hash = self._hash_call(trace.agent_name, trace.input_prompt)
        if call_hash in self._recent_calls:
            results.append(AnomalyResult(
                anomaly_type="loop_detected",
                severity=AnomalySeverity.HIGH,
                layer=AnomalyLayer.BEHAVIOR,
                description=f"Agent '{trace.agent_name}' 对相同输入重复调用——疑似死循环",
                suggestion="检查工具调用逻辑或 Prompt 指令",
                trace_id=trace.trace_id,
                task_id=trace.task_id,
            ))
        self._recent_calls.append(call_hash)
        if len(self._recent_calls) > 100:
            self._recent_calls = self._recent_calls[-50:]

        for tc in trace.tool_calls:
            if not tc.get("tool_name"):
                results.append(AnomalyResult(
                    anomaly_type="invalid_tool_call",
                    severity=AnomalySeverity.HIGH,
                    layer=AnomalyLayer.BEHAVIOR,
                    description=f"Agent '{trace.agent_name}' 调用了未知工具",
                    suggestion="检查工具注册表和 Agent 配置",
                    trace_id=trace.trace_id,
                    task_id=trace.task_id,
                ))

        return results

    # ---- Layer 3: 输出层检测（内容分析器）----

    def _scan_output(self, trace: TraceRecord) -> list[AnomalyResult]:
        results: list[AnomalyResult] = []

        if not trace.output_content or len(trace.output_content.strip()) < 10:
            results.append(AnomalyResult(
                anomaly_type="empty_output",
                severity=AnomalySeverity.MEDIUM,
                layer=AnomalyLayer.OUTPUT,
                description=f"Agent '{trace.agent_name}' 输出过短或为空",
                suggestion="检查 Prompt 指令和上游输入",
                trace_id=trace.trace_id,
                task_id=trace.task_id,
            ))

        return results

    # ---- 工具方法 ----

    @staticmethod
    def _hash_call(agent_name: str, input_prompt: str) -> str:
        raw = f"{agent_name}::{input_prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()

    # ---- 链路级检测 ----

    def check_required_agents(
        self,
        completed_agents: set[str],
        required_agents: set[str],
        task_id: str,
    ) -> list[AnomalyResult]:
        """在所有 Agent 完成后检查关键节点是否缺失。"""
        missing = required_agents - completed_agents
        if missing:
            return [AnomalyResult(
                anomaly_type="missing_required_agent",
                severity=AnomalySeverity.HIGH,
                layer=AnomalyLayer.BEHAVIOR,
                description=f"缺失关键 Agent: {', '.join(sorted(missing))}",
                suggestion="检查任务编排逻辑",
                task_id=task_id,
            )]
        return []
