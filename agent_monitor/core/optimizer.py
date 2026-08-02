"""模块四：结果筛选优化模块。

Pipeline: 异常过滤 → 质量排序 → 多样性去重 → 推荐输出
双通道优化建议：人类可读 + Agent 结构化指令
"""

from dataclasses import dataclass
from difflib import SequenceMatcher

from agent_monitor.core.models import QualityDimension


@dataclass
class RankedResult:
    """排序后的结果条目。"""
    trace_id: str
    agent_name: str
    output_content: str
    quality_score: float
    anomaly_count: int
    rank: int = 0
    recommendation: str = ""  # "adopted" | "alternative" | "archived"


@dataclass
class OptimizationSuggestion:
    """优化建议——双通道。"""
    trace_id: str
    target: str  # "human" | "agent"
    dimension: str
    content: str
    structured_cmd: dict | None = None


# 优化建议模板：面向人类操作者
HUMAN_SUGGESTIONS = {
    QualityDimension.COMPLIANCE: {
        "template": "合规性评分偏低（{score}分）。建议在 System Prompt 中增加合规约束，并确保输出包含风险提示语。",
        "agent_action": {"action": "add_compliance_constraint", "priority": "high"},
    },
    QualityDimension.ACCURACY: {
        "template": "准确性评分偏低（{score}分）。建议增强数据源校验，补充该领域的知识注入。",
        "agent_action": {"action": "enhance_knowledge", "priority": "high"},
    },
    QualityDimension.COMPLETENESS: {
        "template": "完整性评分偏低（{score}分）。输出可能缺少关键检查项，建议增加检查清单。",
        "agent_action": {"action": "add_checklist", "priority": "medium"},
    },
    QualityDimension.RELEVANCE: {
        "template": "相关性评分偏低（{score}分）。建议优化 Prompt 指令，减少 Agent 输出发散空间。",
        "agent_action": {"action": "tighten_prompt", "priority": "medium"},
    },
    QualityDimension.TIMELINESS: {
        "template": "时效性评分偏低（{score}分）。建议确保引用的数据在有效时间窗口内。",
        "agent_action": {"action": "refresh_data", "priority": "low"},
    },
}

# 低分阈值（低于此值生成优化建议）
LOW_SCORE_THRESHOLD = 70


class ResultOptimizer:
    """结果筛选优化器。

    用法:
        optimizer = ResultOptimizer(similarity_threshold=0.95)
        ranked = optimizer.rank(results_with_scores)
        suggestions = optimizer.generate_suggestions(quality_metrics)
    """

    def __init__(self, similarity_threshold: float = 0.95):
        self.similarity_threshold = similarity_threshold

    # ---- 筛选排序 ----

    def rank(
        self,
        results: list[dict],
    ) -> list[RankedResult]:
        """四步 Pipeline：异常过滤 → 质量排序 → 去重 → 推荐。

        Args:
            results: 每个元素包含 trace_id, agent_name, output_content,
                     quality_score, anomaly_count

        Returns:
            排序后的 RankedResult 列表，前 3 有推荐标记。
        """
        # Step 1: 异常过滤
        clean = [r for r in results if r.get("anomaly_count", 0) == 0]

        # Step 2: 质量排序
        clean.sort(key=lambda r: r.get("quality_score", 0), reverse=True)

        # Step 3: 多样性去重
        deduped = self._deduplicate(clean)

        # Step 4: 推荐标记
        ranked = []
        for i, item in enumerate(deduped):
            rr = RankedResult(
                trace_id=item["trace_id"],
                agent_name=item.get("agent_name", ""),
                output_content=item.get("output_content", ""),
                quality_score=item.get("quality_score", 0),
                anomaly_count=item.get("anomaly_count", 0),
                rank=i + 1,
            )
            if i == 0:
                rr.recommendation = "adopted"
            elif i < 3:
                rr.recommendation = "alternative"
            else:
                rr.recommendation = "archived"
            ranked.append(rr)

        return ranked

    def _deduplicate(self, results: list[dict]) -> list[dict]:
        """多样性去重——相似度 > threshold 的只保留得分最高的。"""
        if not results:
            return results

        kept = [results[0]]
        for r in results[1:]:
            is_duplicate = False
            for k in kept:
                sim = SequenceMatcher(
                    None,
                    r.get("output_content", ""),
                    k.get("output_content", ""),
                ).ratio()
                if sim > self.similarity_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                kept.append(r)
        return kept

    # ---- 优化建议 ----

    def generate_suggestions(
        self,
        trace_id: str,
        quality_metrics: dict[str, float],
    ) -> list[OptimizationSuggestion]:
        """根据质量评分生成双通道优化建议。

        Args:
            trace_id: 关联的 trace ID
            quality_metrics: {"accuracy": 85, "completeness": 90, ...}

        Returns:
            优化建议列表（每条包含 human 和 agent 两个版本）。
        """
        suggestions: list[OptimizationSuggestion] = []

        for dimension, score in quality_metrics.items():
            if score < LOW_SCORE_THRESHOLD and dimension in HUMAN_SUGGESTIONS:
                template = HUMAN_SUGGESTIONS[dimension]

                s = OptimizationSuggestion(
                    trace_id=trace_id,
                    target="human",
                    dimension=dimension,
                    content=template["template"].format(score=score),
                )
                suggestions.append(s)

                s = OptimizationSuggestion(
                    trace_id=trace_id,
                    target="agent",
                    dimension=dimension,
                    content=f"Dimension '{dimension}' scored {score}. "
                            f"Recommended action: {template['agent_action']['action']}.",
                    structured_cmd=template["agent_action"],
                )
                suggestions.append(s)

        return suggestions

    def get_top_recommendation(
        self, ranked: list[RankedResult]
    ) -> RankedResult | None:
        """获取最佳推荐结果。"""
        for r in ranked:
            if r.recommendation == "adopted":
                return r
        return ranked[0] if ranked else None
