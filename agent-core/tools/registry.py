"""
工具注册中心
职责：统一管理所有工具，提供工具调用入口
Agent Executor 通过 execute_tool() 调用任意工具
"""

from tools.calculator import calculator
from tools.search     import search
from tools.file_tool  import read_file, write_file
from memory.long_term import LongTermMemory

# ── 工具注册表：工具名 → 处理函数 ────────────────────────
# 新增工具只需在这里注册，无需修改 Executor
TOOL_REGISTRY = {
    "calculator":  calculator,
    "search":      search,
    "read_file":   read_file,
    "write_file":  write_file,
}


async def execute_tool(tool_name: str, tool_input: str) -> str:
    """
    统一工具调用入口
    :param tool_name:  工具名称，必须在 TOOL_REGISTRY 中注册
    :param tool_input: 工具输入参数（字符串）
    :return: 工具执行结果字符串
    """

    # ── memory_save / memory_load 特殊处理 ──────────────
    if tool_name == "memory_save":
        mem = LongTermMemory()
        await mem.save({"task": tool_input, "summary": tool_input, "result": ""})
        return f"已保存到长期记忆：{tool_input}"

    if tool_name == "memory_load":
        mem = LongTermMemory()
        return await mem.load_relevant(tool_input)

    # ── 查找注册的工具 ───────────────────────────────────
    tool_func = TOOL_REGISTRY.get(tool_name)

    if tool_func is None:
        available = ", ".join(TOOL_REGISTRY.keys())
        return f"未知工具: {tool_name}。可用工具: {available}"

    # ── 解析参数并调用 ───────────────────────────────────
    # write_file 需要两个参数（路径 + 内容），用 ||| 分隔
    # 其他工具只需一个字符串参数
    if tool_name == "write_file":
        if "|||" in tool_input:
            path, content = tool_input.split("|||", 1)
            return await tool_func(path.strip(), content.strip())
        else:
            return "write_file 参数格式错误，应为: 文件名 ||| 内容"

    return await tool_func(tool_input)