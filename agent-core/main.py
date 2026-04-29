"""
SmartTask AI Agent - FastAPI 主入口
"""

import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from agent.loop import AgentLoop
from api.routes import router as memory_router
import uvicorn

app = FastAPI(
    title="SmartTask AI Agent",
    description="多步骤 AI Agent 系统",
    version="0.4.0",
)

# ── CORS ───────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册记忆管理路由 ───────────────────────────────────
app.include_router(memory_router)

# ── 请求模型 ───────────────────────────────────────────
class TaskRequest(BaseModel):
    task: str
    session_id: str = "default"


# ── ✅ 新增：首页路由（关键） ───────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <h1>🚀 SmartTask AI Agent 已上线</h1>
    <p>服务运行正常</p>
    <p><a href="/docs">进入 API 文档</a></p>
    """


# ── 健康检查 ───────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.4.0"}


# ── 调试环境变量 ───────────────────────────────────────
@app.get("/debug/env")
async def debug_env():
    return {
        "SERPER_API_KEY": os.getenv("SERPER_API_KEY", "未设置"),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "未设置"),
        "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY", "未设置"),
    }


# ── Agent 执行 ─────────────────────────────────────────
@app.post("/api/agent/run")
async def run_agent(request: TaskRequest):
    if not request.task.strip():
        raise HTTPException(status_code=400, detail="任务内容不能为空")
    try:
        agent = AgentLoop()
        result = await agent.run(
            task=request.task,
            session_id=request.session_id,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── 启动 ───────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Railway 推荐默认 8080
    uvicorn.run("main:app", host="0.0.0.0", port=port)