"""摘要生成器 - 多 provider 降级 + 本地模型兜底"""

from __future__ import annotations

import json
import logging
from typing import Protocol

import httpx

from context_bridge.config import LocalConfig, ProviderConfig
from context_bridge.core import Conversation, ContextSummary

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """请分析以下 AI 编程助手的对话记录，生成一份结构化的上下文摘要。

要求：
1. 总结对话的核心目标和当前进度
2. 列出关键的技术决策及其原因
3. 列出尚未完成的任务
4. 列出已修改的文件路径

请严格按以下 JSON 格式返回（不要包含 markdown 代码块标记）：
{{
  "summary": "对话摘要...",
  "key_decisions": ["决策1", "决策2"],
  "pending_tasks": ["任务1", "任务2"],
  "files_modified": ["path/to/file1", "path/to/file2"]
}}

对话内容：
{conversation}
"""


class LLMProvider(Protocol):
    def chat(self, prompt: str) -> str: ...


class CloudProvider:
    def __init__(self, config: ProviderConfig):
        self.name = config.name
        self.api_key = config.api_key
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model
        self._client = httpx.Client(timeout=120)

    def chat(self, prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        resp = self._client.post(url, json=payload, headers=headers)
        if resp.status_code == 429:
            raise QuotaExhausted(f"{self.name}: 额度用尽 (429)")
        resp.raise_for_status()

        data = resp.json()
        return data["choices"][0]["message"]["content"]


class OllamaProvider:
    def __init__(self, config: LocalConfig):
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model
        self._client = httpx.Client(timeout=300)

    def chat(self, prompt: str) -> str:
        resp = self._client.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return resp.json()["response"]


class QuotaExhausted(Exception):
    pass


class Summarizer:
    def __init__(
        self,
        providers: list[ProviderConfig] | None = None,
        local_config: LocalConfig | None = None,
    ):
        self._cloud_providers: list[CloudProvider] = []
        self._local_provider: OllamaProvider | None = None

        for p in providers or []:
            if p.enabled and p.api_key:
                self._cloud_providers.append(CloudProvider(p))

        if local_config and local_config.enabled:
            self._local_provider = OllamaProvider(local_config)

    def summarize(self, conversation: Conversation) -> ContextSummary:
        conversation_text = conversation.to_text()
        prompt = SUMMARY_PROMPT.format(conversation=conversation_text)

        raw = self._call_with_fallback(prompt)
        parsed = self._parse_response(raw)

        return ContextSummary(
            agent=conversation.agent,
            session_id=conversation.session_id,
            summary=parsed.get("summary", raw),
            key_decisions=parsed.get("key_decisions", []),
            pending_tasks=parsed.get("pending_tasks", []),
            files_modified=parsed.get("files_modified", []),
        )

    def _call_with_fallback(self, prompt: str) -> str:
        errors: list[str] = []

        # 按配置顺序尝试云端 provider
        for provider in self._cloud_providers:
            try:
                logger.info(f"尝试使用 {provider.name} 生成摘要...")
                return provider.chat(prompt)
            except QuotaExhausted as e:
                errors.append(str(e))
                logger.warning(f"{provider.name} 额度用尽，尝试下一个")
            except Exception as e:
                errors.append(f"{provider.name}: {e}")
                logger.warning(f"{provider.name} 调用失败: {e}")

        # 兜底到本地模型
        if self._local_provider:
            try:
                logger.info("使用本地模型生成摘要...")
                return self._local_provider.chat(prompt)
            except Exception as e:
                errors.append(f"本地模型: {e}")

        raise RuntimeError(f"所有摘要提供者均失败:\n" + "\n".join(errors))

    def _parse_response(self, raw: str) -> dict:
        # 尝试提取 JSON
        text = raw.strip()
        # 去除 markdown 代码块标记
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试找到 JSON 部分
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {"summary": text}
