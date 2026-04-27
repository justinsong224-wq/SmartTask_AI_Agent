"""
LLM 统一调用客户端
支持：DashScope (Qwen) / HuggingFace Inference API
职责：屏蔽不同 LLM 提供商的 API 差异，对上层提供统一的 chat() 接口
"""

import os
import httpx
from typing import Optional

# 从环境变量读取配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "dashscope")
LLM_MODEL    = os.getenv("LLM_MODEL", "qwen-turbo")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
HF_API_KEY   = os.getenv("HF_API_KEY", "")
AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "60"))


class LLMClient:
    """
    统一 LLM 客户端
    使用方式：
        client = LLMClient()
        response = await client.chat(messages=[{"role":"user","content":"你好"}])
    """

    def __init__(self):
        self.provider = LLM_PROVIDER
        self.model    = LLM_MODEL

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        发送对话请求，返回模型文本响应
        :param messages: 对话历史，格式 [{"role": "user/assistant", "content": "..."}]
        :param temperature: 生成随机性，0=确定性最强，1=最随机
        :param max_tokens: 最大输出 token 数
        :param system_prompt: 系统提示词（可选，覆盖默认）
        :return: 模型返回的纯文本字符串
        """
        if self.provider == "dashscope":
            return await self._call_dashscope(messages, temperature, max_tokens, system_prompt)
        elif self.provider == "huggingface":
            return await self._call_huggingface(messages, temperature, max_tokens, system_prompt)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {self.provider}")

    # ── DashScope (Qwen) ──────────────────────────────────────────
    async def _call_dashscope(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str],
    ) -> str:
        """调用阿里云 DashScope Qwen API"""

        # 构建消息列表（如有系统提示词，插入开头）
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "input": {"messages": full_messages},
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message",
            },
        }

        async with httpx.AsyncClient(timeout=AGENT_TIMEOUT) as client:
            resp = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # 解析响应
        try:
            return data["output"]["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"DashScope 响应解析失败: {data}") from e

    # ── HuggingFace Inference API ─────────────────────────────────
    async def _call_huggingface(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str],
    ) -> str:
        """调用 HuggingFace Inference API"""

        # HF 使用 OpenAI 兼容格式
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=AGENT_TIMEOUT) as client:
            resp = await client.post(
                "https://api-inference.huggingface.co/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {HF_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"HuggingFace 响应解析失败: {data}") from e


# 全局单例（整个应用共用一个实例）
llm_client = LLMClient()