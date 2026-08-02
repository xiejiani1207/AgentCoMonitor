"""FastAPI 应用入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_monitor.api.routes import router

app = FastAPI(
    title="AgentCoMonitor API",
    description="跨智能体协同执行智能监控与结果筛选优化系统",
    version="0.1.0",
)

# CORS：允许 Dashboard 前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
