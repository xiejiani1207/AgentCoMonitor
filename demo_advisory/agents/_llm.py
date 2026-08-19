"""Demo Agent 共享 LLM 工具——不依赖 agent_monitor。"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()  # 加载项目根目录的 .env

# 模块级指令缓存：由 orchestrator（demo_service）在跑图前注入
# 结构: {agent_name: [instruction_text, ...]}
_ACTIVE_INSTRUCTIONS: dict[str, list[str]] = {}


def set_active_instructions(instructions: dict[str, list[str]]) -> None:
    """注入监控反馈的活跃优化指令（由 orchestrator 在每次跑图前调用）。"""
    _ACTIVE_INSTRUCTIONS.clear()
    _ACTIVE_INSTRUCTIONS.update(instructions)


def get_llm(temperature: float = 0.1):
    """创建 LLM 实例——优先 DEMO_LLM_*，回退 AM_LLM_*。"""
    return ChatOpenAI(
        model=os.environ.get("DEMO_LLM_MODEL") or os.environ.get("AM_LLM_MODEL", "deepseek-chat"),
        api_key=os.environ.get("DEMO_LLM_API_KEY") or os.environ.get("AM_LLM_API_KEY", ""),
        base_url=os.environ.get("DEMO_LLM_BASE_URL") or os.environ.get("AM_LLM_BASE_URL", "https://api.deepseek.com/v1"),
        temperature=temperature,
    )


def load_prompt(name: str) -> str:
    """加载 prompts/ 目录下的 System Prompt，并注入该 Agent 的活跃优化指令。"""
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", name)
    with open(path, "r", encoding="utf-8") as f:
        prompt = f.read()

    agent_name = name.removesuffix(".md")
    instructions = _ACTIVE_INSTRUCTIONS.get(agent_name, [])
    if instructions:
        block = "\n".join(f"- {i}" for i in instructions)
        prompt += f"\n\n## 动态优化指令（来自监控平台反馈，请务必遵守）\n{block}"
    return prompt
