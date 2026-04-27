"""
步骤执行模块
职责：逐步执行计划中的每个子任务，必要时调用工具
"""

from llm.client import llm_client
from llm.prompts import EXECUTOR_SYSTEM, EXECUTOR_USER
from llm.parser import parse_step_result
from tools.registry import execute_tool


class Executor:
    """
    步骤执行器
    使用方式：
        executor = Executor()
        result = await executor.execute_step(step, original_task, previous_conclusions)
    """

    async def execute_step(
        self,
        step: dict,
        original_task: str,
        previous_conclusions: list[str],
        total_steps: int,
    ) -> dict:
        """
        执行单个步骤
        :param step: 计划中的单个步骤字典
        :param original_task: 原始任务（提供上下文）
        :param previous_conclusions: 已完成步骤的结论列表
        :param total_steps: 总步骤数
        :return: 步骤执行结果字典
        """
        tool_result = ""

        # ── 如果该步骤需要调用工具 ──────────────────────
        if step.get("need_tool") and step.get("tool_name"):
            tool_name  = step["tool_name"]
            tool_input = step.get("tool_input", "")

            print(f"  🔧 调用工具: {tool_name}({tool_input})")

            try:
                tool_result = await execute_tool(tool_name, tool_input)
                tool_result = f"工具 [{tool_name}] 返回结果：\n{tool_result}"
            except Exception as e:
                tool_result = f"工具调用失败: {str(e)}"

        # ── 构建 Executor 提示词 ────────────────────────
        user_message = EXECUTOR_USER.format(
            original_task=original_task,
            step_description=step["description"],
            step_id=step["step_id"],
            total_steps=total_steps,
            tool_result=tool_result or "本步骤无工具调用",
            previous_conclusions="\n".join(previous_conclusions) or "这是第一步",
        )

        # ── 调用 LLM 生成本步骤结论 ─────────────────────
        raw_response = await llm_client.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=EXECUTOR_SYSTEM,
            temperature=0.5,
            max_tokens=1024,
        )

        result = parse_step_result(raw_response)
        result["tool_used"]   = step.get("tool_name")
        result["tool_result"] = tool_result

        return result