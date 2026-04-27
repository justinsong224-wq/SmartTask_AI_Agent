"""
网络搜索工具
使用 Serper.dev API（Google 搜索结果，免费2500次/月）
"""

import os
import httpx

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPER_URL     = "https://google.serper.dev/search"


async def search(query: str, max_results: int = 5) -> str:
    """
    调用 Serper.dev 搜索 Google，返回结构化结果
    :param query: 搜索关键词
    :param max_results: 返回条数
    :return: 格式化搜索结果字符串
    """
    if not query.strip():
        return "搜索关键词不能为空"

    if not SERPER_API_KEY:
        return "搜索工具未配置：请在 .env 中设置 SERPER_API_KEY"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                SERPER_URL,
                headers={
                    "X-API-KEY": SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "q": query,
                    "num": max_results,
                    "hl": "zh-cn",   # 优先中文结果
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return _format_results(query, data)

    except httpx.TimeoutException:
        return f"搜索超时：{query}"
    except Exception as e:
        return f"搜索失败：{str(e)}"


def _format_results(query: str, data: dict) -> str:
    """将 Serper 返回的原始数据格式化为可读字符串"""
    output = f"搜索关键词：{query}\n\n"

    # ── 知识图谱（直接答案，如价格、天气等）────────────
    if "knowledgeGraph" in data:
        kg = data["knowledgeGraph"]
        output += f"📌 直接答案：{kg.get('title','')} — {kg.get('description','')}\n\n"

    # ── Answer Box（精选摘要，命中率最高）───────────────
    if "answerBox" in data:
        ab = data["answerBox"]
        answer = ab.get("answer") or ab.get("snippet", "")
        if answer:
            output += f"✅ 精选答案：{answer}\n\n"

    # ── 普通搜索结果 ─────────────────────────────────────
    results = data.get("organic", [])
    if results:
        output += "搜索结果：\n"
        for i, r in enumerate(results, 1):
            output += f"【{i}】{r.get('title', '无标题')}\n"
            output += f"    {r.get('snippet', '无摘要')[:200]}\n"
            output += f"    链接：{r.get('link', '')}\n\n"

    if not results and "answerBox" not in data and "knowledgeGraph" not in data:
        output += f"未找到关于 '{query}' 的搜索结果"

    return output