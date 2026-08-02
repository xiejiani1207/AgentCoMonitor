"""模块三：输出质量评估模块——五维度两层打分。

规则层（< 50ms，无 LLM 调用）→ LLM-as-Judge（深度语义评估）
"""

from dataclasses import dataclass, field

from agent_monitor.core.models import QualityDimension, TraceRecord

# 金融投顾场景默认权重
DEFAULT_WEIGHTS = QualityDimension.DEFAULT_WEIGHTS

# 合规关键词黑名单
COMPLIANCE_BLACKLIST = [
    "保证收益", "稳赚", "无风险", "绝不亏损", "必然", "绝对",
    "肯定会上涨", "包赚", "保本", "零风险",
]


@dataclass
class QualityResult:
    """质量评估结果（轻量级，非 ORM）。"""
    trace_id: str
    accuracy: float | None = None
    completeness: float | None = None
    relevance: float | None = None
    compliance: float | None = None
    timeliness: float | None = None
    overall_score: float = 0.0
    eval_method: str = "rule"
    eval_detail: dict = field(default_factory=dict)


class QualityAssessor:
    """输出质量评估器。

    用法:
        assessor = QualityAssessor(weights=DEFAULT_WEIGHTS)
        result = assessor.evaluate(trace)
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        use_llm: bool = False,
    ):
        self.weights = weights or DEFAULT_WEIGHTS
        self.use_llm = use_llm

    def evaluate(self, trace: TraceRecord) -> QualityResult:
        """两层评估：规则快速过滤 + LLM 深度评估（可选）。"""
        result = QualityResult(trace_id=trace.trace_id)

        # Layer 1: 规则检查（始终执行）
        result.compliance = self._check_compliance(trace)
        result.completeness = self._check_completeness(trace)
        result.timeliness = self._check_timeliness(trace)

        # 如果第一层发现严重合规问题，跳过第二层
        if result.compliance is not None and result.compliance < 40:
            result.eval_method = "rule_only"
            result.eval_detail["skip_reason"] = "合规风险过高，跳过 LLM 评估"
            result.overall_score = self._compute_overall(result)
            return result

        # Layer 2: 评估（规则估算 或 LLM-as-Judge）
        if self.use_llm:
            result.accuracy = self._estimate_accuracy(trace)
            result.relevance = self._estimate_relevance(trace)
            result.eval_method = "rule"  # 同步方法用 rule；异步用 evaluate_async
        else:
            result.accuracy = self._estimate_accuracy(trace)
            result.relevance = self._estimate_relevance(trace)
            result.eval_method = "rule"

        result.overall_score = self._compute_overall(result)
        return result

    async def evaluate_async(self, trace: TraceRecord) -> QualityResult:
        """异步评估——Layer 2 使用 LLM-as-Judge 真实打分。"""
        from agent_monitor.core.llm_client import llm_judge

        result = QualityResult(trace_id=trace.trace_id)

        # Layer 1: 规则检查
        result.compliance = self._check_compliance(trace)
        result.completeness = self._check_completeness(trace)
        result.timeliness = self._check_timeliness(trace)

        if result.compliance is not None and result.compliance < 40:
            result.eval_method = "rule_only"
            result.overall_score = self._compute_overall(result)
            return result

        # Layer 2: LLM-as-Judge
        try:
            accuracy_score = await llm_judge(
                task="评估以下内容的准确性：事实是否正确，有无编造，引用是否准确。",
                content=trace.output_content or "",
                criteria="100分=完全准确，0分=全是编造。给出0-100的数字。",
            )
            result.accuracy = float(accuracy_score)
        except Exception:
            result.accuracy = self._estimate_accuracy(trace)

        try:
            relevance_score = await llm_judge(
                task="评估以下内容与输入问题的相关性：是否紧扣主题，有无跑题。",
                content=f"输入: {trace.input_prompt or ''}\n\n输出: {trace.output_content or ''}",
                criteria="100分=完全相关，0分=完全跑题。给出0-100的数字。",
            )
            result.relevance = float(relevance_score)
        except Exception:
            result.relevance = self._estimate_relevance(trace)

        result.eval_method = "hybrid"
        result.overall_score = self._compute_overall(result)
        return result

    # ---- Layer 1: 规则检查 ----

    def _check_compliance(self, trace: TraceRecord) -> float:
        """合规性检测——关键词黑名单扫描，返回 0-100 分。"""
        output = trace.output_content or ""
        violations = [kw for kw in COMPLIANCE_BLACKLIST if kw in output]
        if not violations:
            return 100.0
        # 每发现一个违规词扣 25 分，最低 0
        score = max(0, 100 - len(violations) * 25)
        return float(score)

    def _check_completeness(self, trace: TraceRecord) -> float:
        """完整性检测——检查输出是否包含基本要素。"""
        output = trace.output_content or ""
        if not output.strip():
            return 0.0
        score = 100.0
        if len(output) < 50:
            score -= 30
        # 检查是否有结论性内容（简化规则）
        if "建议" not in output and "结论" not in output and "分析" not in output:
            score -= 30
        return max(0.0, score)

    def _check_timeliness(self, trace: TraceRecord) -> float:
        """时效性检测——检查是否有时间相关标记。"""
        output = trace.output_content or ""
        # 简化：检查是否包含日期/时间引用
        import re
        if re.search(r"\d{4}[-/]\d{2}[-/]\d{2}", output):
            return 100.0
        if any(word in output for word in ["近期", "当前", "最新", "今年", "本月"]):
            return 80.0
        return 100.0  # 无时间信息时不扣分

    # ---- Layer 2: 语义评估（当前为估算，后续接入 LLM）----

    def _estimate_accuracy(self, trace: TraceRecord) -> float:
        """准确性估算——基于输出长度和格式的启发式评估。"""
        output = trace.output_content or ""
        if not output.strip():
            return 0.0
        score = 80.0
        # 输出较长说明信息量足
        if len(output) > 100:
            score += 10
        if len(output) > 500:
            score += 10
        return min(100.0, score)

    def _estimate_relevance(self, trace: TraceRecord) -> float:
        """相关性估算——检查输出是否与输入有关联。"""
        if not trace.input_prompt or not trace.output_content:
            return 50.0
        # 简化：输入中的关键词出现在输出中
        input_words = set(trace.input_prompt[:200].split())
        output_words = set((trace.output_content or "")[:500].split())
        if not input_words:
            return 80.0
        overlap = len(input_words & output_words) / len(input_words)
        if overlap > 0.3:
            return 100.0
        if overlap > 0.1:
            return 80.0
        return 60.0

    # ---- 综合评分 ----

    def _compute_overall(self, result: QualityResult) -> float:
        scores = {
            "accuracy": result.accuracy,
            "completeness": result.completeness,
            "relevance": result.relevance,
            "compliance": result.compliance,
            "timeliness": result.timeliness,
        }
        weighted = 0.0
        total_weight = 0.0
        for dim, score in scores.items():
            if score is not None:
                w = self.weights.get(dim)
                if w is None:  # 未配置权重的维度不参与计算
                    continue
                weighted += score * w
                total_weight += w
        if total_weight == 0:
            return 0.0
        return round(weighted / total_weight, 2)
