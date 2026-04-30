"""会话管理 - 保存和恢复上下文"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from context_bridge.core import AgentType, ContextSummary


class SessionManager:
    def __init__(self, storage_dir: Path | None = None):
        self._dir = storage_dir or Path.home() / ".context-bridge" / "sessions"
        self._dir.mkdir(parents=True, exist_ok=True)

    @property
    def storage_dir(self) -> Path:
        return self._dir

    def save(self, summary: ContextSummary) -> Path:
        data = {
            "agent": summary.agent.value,
            "session_id": summary.session_id,
            "summary": summary.summary,
            "key_decisions": summary.key_decisions,
            "pending_tasks": summary.pending_tasks,
            "files_modified": summary.files_modified,
            "created_at": summary.created_at.isoformat(),
        }
        filename = f"{summary.agent.value}_{summary.session_id}_{datetime.now():%Y%m%d_%H%M%S}.json"
        path = self._dir / filename
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self, path: Path) -> ContextSummary:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ContextSummary(
            agent=AgentType(data["agent"]),
            session_id=data["session_id"],
            summary=data["summary"],
            key_decisions=data.get("key_decisions", []),
            pending_tasks=data.get("pending_tasks", []),
            files_modified=data.get("files_modified", []),
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    def list_recent(self, agent: AgentType | None = None, limit: int = 10) -> list[Path]:
        files = sorted(self._dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if agent:
            files = [f for f in files if f.name.startswith(agent.value)]
        return files[:limit]

    def build_resume_prompt(self, summary: ContextSummary) -> str:
        parts = [
            "## 之前的对话上下文摘要\n",
            summary.summary,
        ]
        if summary.key_decisions:
            parts.append("\n### 关键决策")
            for d in summary.key_decisions:
                parts.append(f"- {d}")
        if summary.pending_tasks:
            parts.append("\n### 待完成任务")
            for t in summary.pending_tasks:
                parts.append(f"- {t}")
        if summary.files_modified:
            parts.append("\n### 已修改文件")
            for f in summary.files_modified:
                parts.append(f"- {f}")
        parts.append("\n请基于以上上下文继续工作。")
        return "\n".join(parts)
