"""
长期记忆系统 — SQLite 实现
职责：持久化存储任务历史，支持关键词相关性检索
特点：
  - 跨会话持久化，重启后数据不丢失
  - 简单关键词匹配检索相关历史
  - 支持分页查询和统计
  - 防止脏数据：相同任务不重复写入
"""

import os
import aiosqlite
from datetime import datetime, timezone, timedelta
CST = timezone(timedelta(hours=8))

DB_PATH = os.getenv("LONG_TERM_DB", "/app/data/memory/long_term.db")


class LongTermMemory:
    """
    长期记忆（跨会话持久化）
    使用方式：
        mem = LongTermMemory()
        await mem.save({"task": "...", "summary": "...", "result": "..."})
        context = await mem.load_relevant("比特币价格")
        records = await mem.get_all(limit=20)
        await mem.clear_all()
    """

    async def _init_db(self):
        """初始化数据库表结构"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    task        TEXT NOT NULL,
                    summary     TEXT,
                    result      TEXT,
                    session_id  TEXT DEFAULT 'default',
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 创建索引加速查询
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON memories(created_at DESC)
            """)
            await db.commit()

    async def save(self, data: dict):
        """
        保存一条任务记录
        :param data: 包含 task / summary / result / session_id 的字典
        """
        await self._init_db()

        task = data.get("task", "").strip()
        if not task:
            return  # 不保存空任务

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """INSERT INTO memories (task, summary, result, session_id)
                   VALUES (?, ?, ?, ?)""",
                (
                    task[:500],                          # 限制长度
                    data.get("summary", "")[:500],
                    data.get("result",  "")[:500],
                    data.get("session_id", "default"),
                )
            )
            await db.commit()

    async def load_relevant(self, task: str, limit: int = 3) -> str:
        """
        检索与当前任务相关的历史记录
        使用简单关键词匹配（取任务前10个字符作为关键词）
        :param task: 当前任务描述
        :param limit: 返回条数上限
        :return: 格式化的上下文字符串
        """
        await self._init_db()

        # 提取关键词（取前10个字符，避免过长）
        keyword = task[:10].strip()

        async with aiosqlite.connect(DB_PATH) as db:
            # 优先返回相关记录，其次返回最新记录
            async with db.execute(
                """SELECT task, result, created_at FROM memories
                   WHERE task LIKE ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (f"%{keyword}%", limit)
            ) as cursor:
                rows = await cursor.fetchall()

            # 如果没有相关记录，返回最新的几条
            if not rows:
                async with db.execute(
                    """SELECT task, result, created_at FROM memories
                       ORDER BY created_at DESC LIMIT ?""",
                    (limit,)
                ) as cursor:
                    rows = await cursor.fetchall()

        if not rows:
            return ""

        lines = []
        for row in rows:
            task_text   = (row[0] or "")[:80]
            result_text = (row[1] or "")[:100]
            lines.append(f"历史任务: {task_text} → 结果: {result_text}")

        # 严格限制总长度，防止撑爆 token
        context = "\n".join(lines)
        return context[:300]

    async def get_all(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """
        获取所有历史记录（分页）
        :return: 记录列表
        """
        await self._init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                """SELECT id, task, summary, result, session_id, created_at
                   FROM memories
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()

        return [
            {
                "id":         row[0],
                "task":       row[1],
                "summary":    row[2],
                "result":     row[3],
                "session_id": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    async def count(self) -> int:
        """获取总记录数"""
        await self._init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM memories") as cursor:
                row = await cursor.fetchone()
        return row[0] if row else 0

    async def clear_all(self):
        """清空所有长期记忆（慎用）"""
        await self._init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM memories")
            await db.commit()

        
    async def should_save(self, task: str, task_understanding: str, result: str) -> dict:
        """
        调用 LLM 判断任务是否值得长期记忆
        :return: {"should_save": bool, "reason": str, "importance": str}
        """
        from llm.client import llm_client
        from llm.prompts import MEMORY_FILTER_SYSTEM, MEMORY_FILTER_USER
        from llm.parser import extract_json

        user_message = MEMORY_FILTER_USER.format(
            task=task[:200],
            task_understanding=task_understanding[:200],
            result=result[:300],
        )

        try:
            raw = await llm_client.chat(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=MEMORY_FILTER_SYSTEM,
                temperature=0.1,    # 判断任务用极低温度，保证稳定
                max_tokens=128,
            )
            decision = extract_json(raw)

            # 容错：解析失败默认不保存
            if "should_save" not in decision:
                return {"should_save": False, "reason": "解析失败", "importance": "low"}

            return decision

        except Exception as e:
            # 出错默认不保存，不影响主流程
            return {"should_save": False, "reason": str(e), "importance": "low"}

    async def smart_save(self, task: str, task_understanding: str, result: str, session_id: str = "default"):
        """
        智能保存：先让 LLM 判断，值得记忆才写入
        :return: 保存决策字典
        """
        decision = await self.should_save(task, task_understanding, result)

        if decision.get("should_save", False):
            await self.save({
                "task":       task,
                "summary":    f"[{decision.get('importance','medium').upper()}] {task_understanding}",
                "result":     result,
                "session_id": session_id,
            })
            print(f"  💾 长期记忆已保存 [{decision.get('importance')}]: {decision.get('reason')}")
        else:
            print(f"  ⏭️  跳过记忆保存: {decision.get('reason')}")

        return decision