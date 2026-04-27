"""
短期记忆系统 — Redis 实现
职责：存储当前会话的对话历史和步骤记录，会话结束后自动过期
特点：
  - 按 session_id 隔离，不同用户互不干扰
  - TTL 自动过期，无需手动清理
  - 支持获取最近 N 条记录作为上下文
"""

import json
import os
from datetime import datetime
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_TTL = int(os.getenv("REDIS_TTL", "3600"))  # 默认1小时过期


class ShortTermMemory:
    """
    短期记忆（会话级）
    使用方式：
        mem = ShortTermMemory()
        await mem.update("session-001", {"step": 1, "result": "..."})
        history = await mem.get("session-001")
        await mem.clear("session-001")
    """

    def __init__(self):
        self._client = None

    async def _get_client(self):
        """懒加载 Redis 客户端（避免启动时连接失败）"""
        if self._client is None:
            self._client = redis.from_url(REDIS_URL, decode_responses=True)
        return self._client

    async def update(self, session_id: str, data: dict):
        """
        追加一条步骤记录到会话历史
        :param session_id: 会话 ID
        :param data: 步骤数据字典
        """
        client = await self._get_client()
        key = f"session:{session_id}:steps"

        # 加入时间戳
        data["timestamp"] = datetime.now().isoformat()

        # 从左侧推入（最新的在前面）
        await client.lpush(key, json.dumps(data, ensure_ascii=False))

        # 只保留最近 20 条，防止无限增长
        await client.ltrim(key, 0, 19)

        # 重置过期时间
        await client.expire(key, REDIS_TTL)

    async def get(self, session_id: str, limit: int = 10) -> list[dict]:
        """
        获取会话历史记录
        :param session_id: 会话 ID
        :param limit: 返回条数
        :return: 步骤记录列表（最新的在前）
        """
        try:
            client = await self._get_client()
            key = f"session:{session_id}:steps"
            items = await client.lrange(key, 0, limit - 1)
            return [json.loads(i) for i in items]
        except Exception:
            return []

    async def get_context_string(self, session_id: str) -> str:
        """
        获取格式化的上下文字符串，用于注入 Prompt
        """
        history = await self.get(session_id, limit=5)
        if not history:
            return "暂无本次会话历史"

        lines = []
        for item in reversed(history):  # 时间正序
            lines.append(f"步骤{item.get('step','?')}: {item.get('task','')} → {item.get('result','')}")
        return "\n".join(lines)

    async def clear(self, session_id: str):
        """清空指定会话的短期记忆"""
        client = await self._get_client()
        key = f"session:{session_id}:steps"
        await client.delete(key)

    async def get_all_sessions(self) -> list[str]:
        """获取所有活跃会话 ID 列表"""
        client = await self._get_client()
        keys = await client.keys("session:*:steps")
        # 从 "session:xxx:steps" 提取 xxx
        return [k.split(":")[1] for k in keys]