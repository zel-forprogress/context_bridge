"""核心数据结构"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class AgentType(str, Enum):
    CODEX = "codex"
    CLAUDE = "claude"
    CURSOR = "cursor"
    CLINE = "cline"


@dataclass
class Message:
    role: str  # user / assistant / system
    content: str
    timestamp: datetime | None = None
    token_count: int = 0


@dataclass
class Conversation:
    agent: AgentType
    session_id: str
    file_path: Path
    messages: list[Message] = field(default_factory=list)
    total_tokens: int = 0
    max_tokens: int = 200_000
    last_activity: datetime | None = None

    @property
    def usage_ratio(self) -> float:
        if self.max_tokens <= 0:
            return 0.0
        return self.total_tokens / self.max_tokens

    @property
    def is_near_limit(self) -> bool:
        return self.usage_ratio > 0.85

    def to_text(self, max_chars: int = 100_000) -> str:
        lines: list[str] = []
        for msg in self.messages:
            lines.append(f"[{msg.role}]: {msg.content}")
        text = "\n\n".join(lines)
        if len(text) > max_chars:
            text = text[-max_chars:]
        return text


@dataclass
class AgentDetectionResult:
    name: str
    detected: bool
    path: str
    conversation_count: int


@dataclass
class ContextSummary:
    agent: AgentType
    session_id: str
    summary: str
    key_decisions: list[str] = field(default_factory=list)
    pending_tasks: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
