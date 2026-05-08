"""解析器基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from context_bridge.core import Conversation

_SYSTEM_CTX_TAGS = (
    "<permissions instructions>",
    "<app-context>",
    "<collaboration_mode>",
    "<skills_instructions>",
    "<plugins_instructions>",
    "<environment_context>",
)


def strip_system_context(text: str) -> str:
    """剥离注入的系统上下文块（如 <app-context>...</app-context>）"""
    result: list[str] = []
    skip = False
    for line in text.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(tag) for tag in _SYSTEM_CTX_TAGS):
            skip = True
            continue
        if skip and stripped.startswith("</"):
            skip = False
            continue
        if not skip:
            result.append(line)
    return "\n".join(result).strip()


class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """判断是否能解析该文件"""
        ...

    @abstractmethod
    def parse(self, file_path: Path) -> Conversation | None:
        """解析对话文件，返回 Conversation 对象"""
        ...

    def estimate_tokens(self, text: str) -> int:
        """粗略估算 token 数（中文约 1.5 字/token，英文约 4 字符/token）"""
        cn_chars = sum(1 for c in text if "一" <= c <= "鿿")
        other_chars = len(text) - cn_chars
        return int(cn_chars / 1.5 + other_chars / 4)
