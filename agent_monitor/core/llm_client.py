"""通用 LLM 客户端——OpenAI 兼容接口。

支持 OpenAI / DeepSeek / 通义千问 等兼容 API。
"""

import logging

import httpx

from agent_monitor.config import settings

logger = logging.getLogger(__name__)

# 复用 HTTP 连接，避免每次调用重新建连（省 TLS 握手开销）
_client = httpx.AsyncClient(timeout=30)


async def llm_chat(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 512,
) -> str:
    """发送一次 LLM 对话，返回回复文本。"""
    if not settings.llm_api_key:
        raise RuntimeError("LLM API key not configured (set AM_LLM_API_KEY)")

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model or settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    resp = await _client.post(
        f"{settings.llm_base_url}/chat/completions",
        headers=headers,
        json=body,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


async def llm_judge(
    task: str,
    content: str,
    criteria: str,
    model: str | None = None,
) -> str:
    """LLM-as-Judge：对内容按标准打分，返回 0-100 的数字。"""
    prompt = (
        f"## 任务\n{task}\n\n"
        f"## 待评估内容\n{content}\n\n"
        f"## 评分标准\n{criteria}\n\n"
        "请给出 0-100 的评分，只返回数字，不要任何解释。"
    )
    try:
        result = await llm_chat(
            system_prompt="你是一个严格的质量评估器。只输出一个 0-100 的整数。",
            user_message=prompt,
            model=model,
        )
        # 解析数字
        import re
        match = re.search(r"\d+", result)
        if match:
            score = int(match.group())
            return min(100, max(0, score))
        return 50  # 无法解析时默认
    except Exception:
        logger.exception("LLM judge failed for task: %s", task)
        return 50
