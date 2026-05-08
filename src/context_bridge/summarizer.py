"""摘要生成器 - 多 provider 降级 + 本地模型兜底"""

from __future__ import annotations

import json
import logging
from typing import Protocol

import httpx
import requests

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
        self.api_type = config.api_type
        self._client = httpx.Client(timeout=120)

    def close(self):
        self._client.close()

    def chat(self, prompt: str) -> str:
        if self.api_type == "anthropic":
            return self._chat_anthropic(prompt)
        else:
            return self._chat_openai(prompt)

    def _chat_openai(self, prompt: str) -> str:
        """OpenAI 格式 API"""
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

    def _chat_anthropic(self, prompt: str) -> str:
        """Anthropic 格式 API"""
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        logger.info(f"调用 Anthropic API: {url}")
        resp = self._client.post(url, json=payload, headers=headers)
        logger.info(f"响应状态码: {resp.status_code}")

        if resp.status_code == 429:
            raise QuotaExhausted(f"{self.name}: 额度用尽 (429)")

        if resp.status_code != 200:
            error_detail = resp.text[:200] if resp.text else "无响应内容"
            logger.error(f"Anthropic API 错误: {resp.status_code} - {error_detail}")
            raise RuntimeError(f"API 调用失败 ({resp.status_code}): {error_detail}")

        resp.raise_for_status()

        data = resp.json()
        return data["content"][0]["text"]


class OllamaProvider:
    def __init__(self, config: LocalConfig):
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model

    def is_available(self) -> bool:
        """检测 Ollama 是否运行且配置的模型已安装"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code != 200:
                return False
            models = [m["name"] for m in resp.json().get("models", [])]
            return self.model in models
        except Exception:
            return False

    def chat(self, prompt: str) -> str:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=300,
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
            provider = OllamaProvider(local_config)
            # 只有在 Ollama 可用且模型已安装时才启用
            if provider.is_available():
                self._local_provider = provider

    @property
    def has_providers(self) -> bool:
        return bool(self._cloud_providers) or self._local_provider is not None

    def close(self):
        for p in self._cloud_providers:
            p.close()

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
