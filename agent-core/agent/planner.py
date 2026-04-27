"""
任务规划模块
职责：接收用户任务，调用 LLM 生成结构化执行计划
"""

from llm.client import llm_client
from llm.prompts import PLANNER_SYSTEM, PLANNER_USER
from llm.parser import parse_plan


class Planner:
    """
    任务规划器
    使用方式：
        planner = Planner()
        plan = await planner.create_plan("帮我查询今天的 BTC 价格并计算涨幅")
    """

    async def create_plan(self, task: str, memory_context: str = "") -> dict:
        """
        为任务生成执行计划
        :param task: 用户原始任务描述
        :param memory_context: 长期记忆中的相关上下文
        :return: 标准化计划字典 {"task_understanding": ..., "steps": [...]}
        """
        # 构建用户消息
        user_message = PLANNER_USER.format(
            task=task,
            memory_context=memory_context or "暂无历史记忆",
        )

        # 调用 LLM 生成计划
        raw_response = await llm_client.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=PLANNER_SYSTEM,
            temperature=0.3,   # 规划阶段用低温度，保证稳定性
            max_tokens=1024,
        )

        # 解析并返回结构化计划
        plan = parse_plan(raw_response)
        return plan