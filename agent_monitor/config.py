from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库 — 默认本地 Docker，生产通过 AM_DATABASE_URL 环境变量覆盖为 Neon
    database_url: str = (
        "postgresql+asyncpg://agentmonitor:agentmonitor@localhost:5432/agent_monitor"
    )
    database_url_sync: str = (
        "postgresql://agentmonitor:agentmonitor@localhost:5432/agent_monitor"
    )

    @property
    def database_connect_args(self) -> dict:
        """如果是 Neon（含 'neon.tech'），自动启用 SSL。"""
        if "neon.tech" in self.database_url:
            return {"ssl": "require"}
        return {}

    # WebSocket
    websocket_heartbeat_interval: int = 30

    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"

    model_config = {
        "env_prefix": "AM_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
