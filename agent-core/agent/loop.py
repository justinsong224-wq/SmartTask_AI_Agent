"""
Agent 主循环控制器
职责：协调 Planner → Executor → Memory → Formatter 的完整执行流程
这是整个 Agent 系统的核心入口
"""

import os
from agent.planner   import Planner
from agent.executor  import Executor
from agent.formatter import Formatter
from memory.short_term import ShortTermMemory
from memory.long_term  import LongTermMemory

MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "10"))


class AgentLoop:
    """
    Agent 主循环
    使用方式：
        agent = AgentLoop()
        result = await agent.run("帮我搜索今天的 AI 新闻并总结")
    """

    def __init__(self):
        self.planner    = Planner()
        self.executor   = Executor()
        self.formatter  = Formatter()
        self.short_mem  = ShortTermMemory()
        self.long_mem   = LongTermMemory()

    async def run(self, task: str, session_id: str = "default") -> dict:
        """
        执行完整 Agent 任务
        :param task: 用户任务描述
        :param session_id: 会话 ID（用于隔离不同用户的短期记忆）
        :return: 包含完整执行结果的字典
        """
        print(f"\n{'='*50}")
        print(f"🚀 Agent 启动 | 任务: {task}")
        print(f"{'='*50}")

        # ── Step 1: 加载记忆上下文 ────────────────────────
        memory_context = await self.long_mem.load_relevant(task)
        print(f"📚 加载长期记忆: {len(memory_context)} 条相关记录")

        # ── Step 2: 规划阶段 ──────────────────────────────
        print("\n📋 [Planner] 生成执行计划...")
        plan = await self.planner.create_plan(task, memory_context)

        task_understanding = plan.get("task_understanding", "")
        steps = plan.get("steps", [])

        # 防止步骤数超过安全上限
        steps = steps[:MAX_STEPS]
        total_steps = len(steps)

        print(f"  理解：{task_understanding}")
        print(f"  步骤数：{total_steps}")

        # ── Step 3: 执行阶段 ──────────────────────────────
        print("\n⚙️  [Executor] 开始逐步执行...")
        execution_log   = []   # 完整执行记录
        conclusions     = []   # 已完成步骤的结论（用于上下文传递）

        for step in steps:
            step_id = step["step_id"]
            print(f"\n  → 步骤 {step_id}/{total_steps}: {step['description']}")

            # 执行单个步骤
            result = await self.executor.execute_step(
                step=step,
                original_task=task,
                previous_conclusions=conclusions,
                total_steps=total_steps,
            )

            # 记录本步骤结论
            conclusion_text = f"步骤{step_id}: {result.get('key_findings', result.get('conclusion', ''))}"
            conclusions.append(conclusion_text)
            execution_log.append({
                "step_id":     step_id,
                "description": step["description"],
                "tool_used":   result.get("tool_used"),
                "conclusion":  result.get("conclusion", ""),
                "success":     result.get("success", True),
            })

            print(f"  ✅ 完成: {result.get('key_findings', '')}")

            # 更新短期记忆
            await self.short_mem.update(session_id, {
                "step": step_id,
                "task": step["description"],
                "result": result.get("key_findings", ""),
            })

        # ── Step 4: 格式化输出 ────────────────────────────
        print("\n📝 [Formatter] 生成最终报告...")
        final_report = await self.formatter.format(
            task=task,
            task_understanding=task_understanding,
            execution_log=execution_log,
        )

        # ── Step 5: 保存长期记忆 ─────────────────────────
        print("\n🧠 [Memory] LLM 判断是否值得长期记忆...")
        final_result = conclusions[-1] if conclusions else ""
        memory_decision = await self.long_mem.smart_save(
            task=task,
            task_understanding=task_understanding,
            result=conclusions[-1] if conclusions else "",
            session_id=session_id,
        )

        print("\n✅ Agent 任务完成！")

        return {
            "task":               task,
            "task_understanding": task_understanding,
            "steps_executed":     total_steps,
            "execution_log":      execution_log,
            "final_report":       final_report,
            "memory_decision":    memory_decision,
            "session_id":         session_id,
        }