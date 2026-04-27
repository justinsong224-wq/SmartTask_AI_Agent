"""
API 数据模型定义
使用 Pydantic 做请求/响应的数据验证
"""

from pydantic import BaseModel
from typing import Optional


# ── 请求模型 ──────────────────────────────────────────
class TaskRequest(BaseModel):
    task:       str
    session_id: str = "default"


# ── 响应模型 ──────────────────────────────────────────
class MemoryRecord(BaseModel):
    id:         int
    task:       str
    summary:    Optional[str]
    result:     Optional[str]
    session_id: str
    created_at: str


class MemoryListResponse(BaseModel):
    total:   int
    records: list[MemoryRecord]


class SessionHistoryResponse(BaseModel):
    session_id: str
    history:    list[dict]