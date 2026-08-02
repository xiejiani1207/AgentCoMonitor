"""Demo Agent 共享 LLM 工具——不依赖 agent_monitor。"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()  # 加载项目根目录的 .env


def get_llm(temperature: float = 0.1):
    """创建 LLM 实例——优先 DEMO_LLM_*，回退 AM_LLM_*。"""
    return ChatOpenAI(
        model=os.environ.get("DEMO_LLM_MODEL") or os.environ.get("AM_LLM_MODEL", "deepseek-chat"),
        api_key=os.environ.get("DEMO_LLM_API_KEY") or os.environ.get("AM_LLM_API_KEY", ""),
        base_url=os.environ.get("DEMO_LLM_BASE_URL") or os.environ.get("AM_LLM_BASE_URL", "https://api.deepseek.com/v1"),
        temperature=temperature,
    )


def load_prompt(name: str) -> str:
    """加载 prompts/ 目录下的 System Prompt 文件。"""
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
