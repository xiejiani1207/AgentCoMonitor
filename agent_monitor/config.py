from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库 — 默认本地 Docker，生产通过 AM_DATABASE_URL 环境变量覆盖为 Neon
    database_url: str = (
        "postgresql+asyncpg://agentmonitor:agentmonitor@localhost:5432/agent_monitor"
    )
    database_url_sync: str = (
        "postgresql://agentmonitor:agentmonitor@localhost:5432/agent_monitor"
    )

    # WebSocket
    websocket_heartbeat_interval: int = 30

    # LLM
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-5"

    model_config = {"env_prefix": "AM_"}


settings = Settings()
