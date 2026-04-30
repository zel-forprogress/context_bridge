"""解析器基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from context_bridge.core import Conversation


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
