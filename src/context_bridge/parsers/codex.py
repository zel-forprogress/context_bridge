"""Codex conversation parser.

Codex stores rollout transcripts as JSONL files under ~/.codex/sessions and
~/.codex/archived_sessions. Each line is an event; user/assistant text lives in
response_item payloads whose payload type is "message".
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from context_bridge.core import AgentType, Conversation, Message
from context_bridge.parsers.base import BaseParser, strip_system_context


class CodexParser(BaseParser):
    def can_parse(self, file_path: Path) -> bool:
        path_text = str(file_path).lower()
        return (
            file_path.suffix == ".jsonl"
            and ".codex" in path_text
            and (
                "sessions" in path_text
                or "archived_sessions" in path_text
                or file_path.name.startswith("rollout-")
            )
        )

    def parse(self, file_path: Path) -> Conversation | None:
        messages: list[Message] = []
        total_tokens = 0
        session_id = file_path.stem
        max_tokens = 200_000

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

                    if entry.get("type") == "session_meta":
                        payload = entry.get("payload") or {}
                        if payload.get("id"):
                            session_id = str(payload["id"])
                        continue

                    payload = entry.get("payload") or {}
                    if (
                        entry.get("type") == "event_msg"
                        and payload.get("type") == "task_started"
                    ):
                        if context_window := payload.get("model_context_window"):
                            try:
                                max_tokens = int(context_window)
                            except (TypeError, ValueError):
                                pass
                        continue

                    if (
                        entry.get("type") != "response_item"
                        or payload.get("type") != "message"
                    ):
                        continue

                    role = payload.get("role", "")
                    if role not in ("user", "assistant", "developer", "system"):
                        continue

                    # 跳过纯系统指令消息
                    if role in ("developer", "system"):
                        continue

                    content = self._extract_content(payload.get("content"))
                    if not content:
                        continue

                    # 剥离 Codex 注入的系统上下文块
                    content = strip_system_context(content)
                    if not content:
                        continue

                    tokens = self.estimate_tokens(content)
                    total_tokens += tokens

                    messages.append(
                        Message(
                            role=role,
                            content=content,
                            timestamp=self._parse_timestamp(entry.get("timestamp")),
                            token_count=tokens,
                        )
                    )
        except (OSError, PermissionError):
            return None

        if not messages:
            return None

        return Conversation(
            agent=AgentType.CODEX,
            session_id=session_id,
            file_path=file_path,
            messages=messages,
            total_tokens=total_tokens,
            max_tokens=max_tokens,
            last_activity=messages[-1].timestamp,
        )

    def _extract_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content

        if not isinstance(content, list):
            return ""

        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue

            if not isinstance(block, dict):
                continue

            text = block.get("text")
            if isinstance(text, str):
                parts.append(text)

        return "\n".join(p for p in parts if p).strip()

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
