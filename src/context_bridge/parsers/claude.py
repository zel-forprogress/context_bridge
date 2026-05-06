"""Claude Code 对话解析器

Claude Code 的对话以 JSONL 格式存储在 ~/.claude/projects/ 下。
每行是一个 JSON 对象，包含 role、content 等字段。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from context_bridge.core import AgentType, Conversation, Message
from context_bridge.parsers.base import BaseParser

_SYSTEM_CTX_TAGS = (
    "<permissions instructions>",
    "<app-context>",
    "<collaboration_mode>",
    "<skills_instructions>",
    "<plugins_instructions>",
    "<environment_context>",
)


def _strip_system_context(text: str) -> str:
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


class ClaudeParser(BaseParser):
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == ".jsonl" and ".claude" in str(file_path)

    def parse(self, file_path: Path) -> Conversation | None:
        messages: list[Message] = []
        total_tokens = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    msg_type = entry.get("type", "")
                    if msg_type not in ("human", "assistant", "user", "message"):
                        continue

                    # 提取文本内容
                    content = self._extract_content(entry)
                    if not content:
                        continue

                    role = "user" if msg_type in ("human", "user") else "assistant"
                    tokens = self.estimate_tokens(content)
                    total_tokens += tokens

                    timestamp = None
                    if ts := entry.get("timestamp"):
                        try:
                            timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        except (ValueError, AttributeError):
                            pass

                    messages.append(
                        Message(
                            role=role,
                            content=content,
                            timestamp=timestamp,
                            token_count=tokens,
                        )
                    )
        except (OSError, PermissionError):
            return None

        if not messages:
            return None

        session_id = file_path.stem
        return Conversation(
            agent=AgentType.CLAUDE,
            session_id=session_id,
            file_path=file_path,
            messages=messages,
            total_tokens=total_tokens,
            last_activity=messages[-1].timestamp,
        )

    def _extract_content(self, entry: dict) -> str:
        """从 Claude Code 的消息条目中提取文本"""
        raw = ""
        # 直接有 content 字段
        if isinstance(entry.get("content"), str):
            raw = entry["content"]
        # content 是列表（多模态格式）
        elif isinstance(entry.get("content"), list):
            parts = []
            for block in entry["content"]:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            raw = "\n".join(parts)
        # message 嵌套
        elif isinstance(entry.get("message"), dict):
            return self._extract_content(entry["message"])

        # 剥离系统上下文块
        if raw:
            raw = _strip_system_context(raw)
        return raw
