"""Cline 对话解析器

Cline 的对话存储在 VS Code 扩展目录下。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from context_bridge.core import AgentType, Conversation, Message
from context_bridge.parsers.base import BaseParser


class ClineParser(BaseParser):
    def can_parse(self, file_path: Path) -> bool:
        return "cline" in str(file_path).lower() and file_path.suffix in (".json", ".jsonl")

    def parse(self, file_path: Path) -> Conversation | None:
        messages: list[Message] = []
        total_tokens = 0

        try:
            text = file_path.read_text(encoding="utf-8")
            data = json.loads(text)

            entries = data if isinstance(data, list) else data.get("messages", [])

            for entry in entries:
                if not isinstance(entry, dict):
                    continue

                role = entry.get("role", "")
                if role not in ("user", "assistant"):
                    continue

                content = entry.get("content", "")
                if isinstance(content, list):
                    content = "\n".join(
                        b.get("text", str(b)) for b in content
                    )

                if not content:
                    continue

                tokens = self.estimate_tokens(content)
                total_tokens += tokens

                timestamp = None
                if ts := entry.get("ts"):
                    try:
                        timestamp = datetime.fromtimestamp(int(ts) / 1000)
                    except (ValueError, TypeError):
                        pass

                messages.append(
                    Message(role=role, content=content, timestamp=timestamp, token_count=tokens)
                )

        except (OSError, json.JSONDecodeError, PermissionError):
            return None

        if not messages:
            return None

        return Conversation(
            agent=AgentType.CLINE,
            session_id=file_path.stem,
            file_path=file_path,
            messages=messages,
            total_tokens=total_tokens,
            last_activity=messages[-1].timestamp,
        )
