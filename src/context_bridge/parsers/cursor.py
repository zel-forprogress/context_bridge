"""Cursor 对话解析器

Cursor 的对话存储在 workspaceStorage 目录下的 SQLite 数据库或 JSON 文件中。
这里处理 JSON 格式的导出文件。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from context_bridge.core import AgentType, Conversation, Message
from context_bridge.parsers.base import BaseParser


class CursorParser(BaseParser):
    def can_parse(self, file_path: Path) -> bool:
        return "cursor" in str(file_path).lower() and file_path.suffix in (".json", ".jsonl")

    def parse(self, file_path: Path) -> Conversation | None:
        messages: list[Message] = []
        total_tokens = 0

        try:
            text = file_path.read_text(encoding="utf-8")
            data = json.loads(text)

            # Cursor 的对话格式可能是数组或对象嵌套
            entries = data if isinstance(data, list) else data.get("messages", data.get("conversation", []))

            for entry in entries:
                if not isinstance(entry, dict):
                    continue

                role = entry.get("role", "unknown")
                if role not in ("user", "assistant", "human"):
                    continue

                content = entry.get("content", "")
                if isinstance(content, list):
                    content = "\n".join(
                        b.get("text", "") for b in content if isinstance(b, dict)
                    )

                if not content:
                    continue

                if role == "human":
                    role = "user"

                tokens = self.estimate_tokens(content)
                total_tokens += tokens

                timestamp = None
                if ts := entry.get("timestamp"):
                    try:
                        timestamp = datetime.fromisoformat(str(ts))
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
            agent=AgentType.CURSOR,
            session_id=file_path.stem,
            file_path=file_path,
            messages=messages,
            total_tokens=total_tokens,
            last_activity=messages[-1].timestamp,
        )
