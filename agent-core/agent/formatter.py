"""
结构化输出模块
职责：将执行记录格式化为 Markdown 报告
"""

from llm.client  import llm_client
from llm.prompts import FORMATTER_SYSTEM, FORMATTER_USER


class Formatter:

    async def format(
        self,
        task: str,
        task_understanding: str,
        execution_log: list[dict],
    ) -> str:
        """
        生成最终 Markdown 报告
        """
        # 构建执行记录文本
        log_text = ""
        for entry in execution_log:
            tool_info = f"（使用工具: {entry['tool_used']}）" if entry.get("tool_used") else ""
            log_text += f"步骤{entry['step_id']}{tool_info}: {entry['description']}\n"
            log_text += f"结论: {entry['conclusion']}\n\n"

        user_message = FORMATTER_USER.format(
            task=task,
            execution_log=log_text,
        )

        report = await llm_client.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=FORMATTER_SYSTEM,
            temperature=0.4,
            max_tokens=2048,
        )

        return report