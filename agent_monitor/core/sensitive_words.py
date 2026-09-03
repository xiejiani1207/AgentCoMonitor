"""敏感词库读取——模块级缓存，供合规检测同步读取。"""

import re

from sqlalchemy import select

from agent_monitor.db.models import SensitiveWord
from agent_monitor.db.session import async_session

# 默认敏感词（DB 尚未加载时的兜底，与历史硬编码黑名单一致）
DEFAULT_SENSITIVE_WORDS = [
    "保证收益", "稳赚", "无风险", "绝不亏损", "必然", "绝对",
    "肯定会上涨", "包赚", "保本", "零风险",
]

_cache: list[str] | None = None


async def refresh_sensitive_words() -> None:
    """从 DB 重新加载敏感词到缓存（每次 chat 前调用一次）。"""
    global _cache
    async with async_session() as session:
        result = await session.execute(select(SensitiveWord.word))
        _cache = [row[0] for row in result.all()]


def get_sensitive_words() -> list[str]:
    """同步获取敏感词（缓存优先，兜底默认列表）。"""
    return _cache if _cache is not None else DEFAULT_SENSITIVE_WORDS


def detect_sensitive_sentences(text: str) -> dict:
    """句级检测文本中命中敏感词的句子。

    Returns:
        {
            "violations": [{"sentence": str, "words": [str, ...]}, ...],
            "matched_words": [str, ...],  # 去重后的所有命中词
            "score": float,               # 100 - 50 * 违规句数，最低 0
        }
    """
    words = get_sensitive_words()
    if not text or not words:
        return {"violations": [], "matched_words": [], "score": 100.0}

    sentences = re.split(r"[。！？!?]", text)
    violations: list[dict] = []
    matched: set[str] = set()
    for raw in sentences:
        sentence = raw.strip()
        if not sentence:
            continue
        hits = [w for w in words if w in sentence]
        if hits:
            violations.append({"sentence": sentence, "words": hits})
            matched.update(hits)

    score = max(0, 100 - 50 * len(violations))
    return {
        "violations": violations,
        "matched_words": list(matched),
        "score": float(score),
    }


def intercept_sentences(text: str, violations: list[dict]) -> str:
    """移除违规句，返回拦截后的干净文本。"""
    if not violations:
        return text
    offending = {v["sentence"] for v in violations}
    # 用捕获分隔符切分，保留标点
    parts = re.split(r"([。！？!?])", text)
    kept: list[str] = []
    for i in range(0, len(parts) - 1, 2):
        sentence = parts[i]
        delim = parts[i + 1]
        if sentence.strip() in offending:
            continue
        kept.append(sentence + delim)
    if len(parts) % 2 == 1 and parts[-1].strip() not in offending:
        kept.append(parts[-1])
    return "".join(kept).strip()
