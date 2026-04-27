"""
记忆管理 API 路由
提供查询、清空记忆的接口，方便调试和管理
"""

from fastapi import APIRouter, HTTPException
from memory.short_term import ShortTermMemory
from memory.long_term  import LongTermMemory

router = APIRouter(prefix="/api/memory", tags=["memory"])

short_mem = ShortTermMemory()
long_mem  = LongTermMemory()


# ── 长期记忆接口 ───────────────────────────────────────

@router.get("/long-term")
async def get_long_term_memory(limit: int = 20, offset: int = 0):
    """获取长期记忆列表（分页）"""
    records = await long_mem.get_all(limit=limit, offset=offset)
    total   = await long_mem.count()
    return {"total": total, "records": records}


@router.delete("/long-term")
async def clear_long_term_memory():
    """清空所有长期记忆"""
    await long_mem.clear_all()
    return {"message": "长期记忆已清空"}

@router.get("/long-term/stats")
async def get_memory_stats():
    """获取记忆统计信息"""
    total = await long_mem.count()
    records = await long_mem.get_all(limit=5)
    return {
        "total_records": total,
        "recent_5": [
            {
                "task":       r["task"][:50],
                "importance": r["summary"][:10] if r["summary"] else "unknown",
                "created_at": r["created_at"],
            }
            for r in records
        ]
    }


# ── 短期记忆接口 ───────────────────────────────────────

@router.get("/short-term/{session_id}")
async def get_short_term_memory(session_id: str):
    """获取指定会话的短期记忆"""
    history = await short_mem.get(session_id)
    return {
        "session_id": session_id, 
        "count":      len(history),
        "history":    history,
    }


@router.delete("/short-term/{session_id}")
async def clear_short_term_memory(session_id: str):
    """清空指定会话的短期记忆"""
    await short_mem.clear(session_id)
    return {"message": f"会话 {session_id} 的短期记忆已清空 ✔"}


@router.get("/sessions")
async def get_all_sessions():
    """获取所有活跃会话列表"""
    sessions = await short_mem.get_all_sessions()
    return {
        "count":    len(sessions),
        "sessions": sessions,
    }