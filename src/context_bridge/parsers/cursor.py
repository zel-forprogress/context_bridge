"""Cursor 对话解析器

Cursor 的本地数据形态会随版本变化。这里支持两类轻量格式：
- projects/**/agent-transcripts/*.txt
- JSON / JSONL 格式的导出文件
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from context_bridge.core import AgentType, Conversation, Message
from context_bridge.parsers.base import BaseParser


class CursorParser(BaseParser):
    def can_parse(self, file_path: Path) -> bool:
        path_text = str(file_path).lower()
        if "cursor" not in path_text:
            return False

        if file_path.suffix == ".txt":
            return file_path.parent.name == "agent-transcripts"

        if file_path.suffix in (".json", ".jsonl"):
            return (
                "workspacestorage" in path_text
                or "agent-transcripts" in path_text
            )

        return False

    def parse(self, file_path: Path) -> Conversation | None:
        if file_path.suffix == ".txt":
            return self._parse_text_transcript(file_path)
        return self._parse_json_export(file_path)

    def _parse_json_export(self, file_path: Path) -> Conversation | None:
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

    def _parse_text_transcript(self, file_path: Path) -> Conversation | None:
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, PermissionError):
            return None

        messages: list[Message] = []
        total_tokens = 0
        current_role: str | None = None
        current_lines: list[str] = []

        def flush_current():
            nonlocal total_tokens
            if current_role is None:
                return
            content = "\n".join(current_lines).strip()
            if not content:
                return
            content = self._strip_cursor_tags(content)
            tokens = self.estimate_tokens(content)
            total_tokens += tokens
            messages.append(
                Message(
                    role=current_role,
                    content=content,
                    token_count=tokens,
                )
            )

        for line in text.splitlines():
            marker = line.strip().lower()
            if marker in ("user:", "assistant:"):
                flush_current()
                current_role = "user" if marker == "user:" else "assistant"
                current_lines = []
                continue
            current_lines.append(line)

        flush_current()

        if not messages:
            return None

        return Conversation(
            agent=AgentType.CURSOR,
            session_id=file_path.stem,
            file_path=file_path,
            messages=messages,
            total_tokens=total_tokens,
            last_activity=datetime.fromtimestamp(file_path.stat().st_mtime),
        )

    def _strip_cursor_tags(self, content: str) -> str:
        return (
            content.replace("<user_query>", "")
            .replace("</user_query>", "")
            .strip()
        )
