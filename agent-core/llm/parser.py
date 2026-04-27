"""
LLM 响应解析器
职责：将 LLM 返回的原始文本解析为结构化 Python 对象
（LLM 有时会在 JSON 外包裹 markdown，需要容错处理）
"""

import json
import re
from typing import Any


def extract_json(text: str) -> dict:
    """
    从 LLM 响应中提取 JSON 对象
    容错处理以下情况：
    - 纯 JSON 字符串
    - ```json ... ``` 代码块包裹
    - JSON 前后有多余文字
    """
    # 先尝试直接解析
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 代码块
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试提取第一个 { ... } 块
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # 全部失败，返回错误结构
    return {
        "error": "JSON 解析失败",
        "raw_text": text[:500],  # 只保留前 500 字符用于调试
    }


def parse_plan(text: str) -> dict:
    """
    解析 Planner 返回的执行计划
    返回标准化的计划字典，包含 task_understanding 和 steps 列表
    """
    data = extract_json(text)

    # 容错：如果解析失败，生成一个单步降级计划
    if "error" in data or "steps" not in data:
        return {
            "task_understanding": "无法解析计划，将直接执行任务",
            "steps": [
                {
                    "step_id": 1,
                    "description": "直接回答用户任务",
                    "need_tool": False,
                    "tool_name": None,
                    "tool_input": None,
                }
            ],
        }
    return data


def parse_step_result(text: str) -> dict:
    """
    解析 Executor 返回的步骤结论
    """
    data = extract_json(text)

    if "error" in data or "conclusion" not in data:
        return {
            "step_id": 0,
            "conclusion": text[:1000],   # 原始文本作为结论
            "success": True,
            "key_findings": "步骤已完成",
        }
    return data