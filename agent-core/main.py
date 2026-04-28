"""
SmartTask AI Agent - FastAPI 主入口
"""

import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.loop import AgentLoop
from api.routes import router as memory_router
import uvicorn

app = FastAPI(
    title="SmartTask AI Agent",
    description="多步骤 AI Agent 系统",
    version="0.4.0",
)

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
    task:       str
    session_id: str = "default"


# ── 路由 ───────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.4.0"}


@app.get("/debug/env")
async def debug_env():
    return {
        "SERPER_API_KEY":    os.getenv("SERPER_API_KEY",    "未设置"),
        "LLM_PROVIDER":      os.getenv("LLM_PROVIDER",      "未设置"),
        "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY", "未设置"),
    }


@app.post("/api/agent/run")
async def run_agent(request: TaskRequest):
    """执行 Agent 任务"""
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


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  # 如果 PORT 未设置，默认 8000
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)