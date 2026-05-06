"""Agent 自动检测 — 扫描已知路径判断哪些 AI Agent 已安装"""

from __future__ import annotations

from pathlib import Path

from context_bridge.core import AgentDetectionResult, AgentType
from context_bridge.parsers import get_parser

AGENT_KNOWN_PATHS: dict[str, list[Path]] = {
    "claude": [
        Path.home() / ".claude",
        Path.home() / ".claude" / "projects",
    ],
    "codex": [
        Path.home() / ".codex" / "sessions",
        Path.home() / ".codex" / "archived_sessions",
    ],
}


def _count_conversations(agent_type: AgentType, search_paths: list[Path]) -> int:
    """遍历目录，用对应 parser 的 can_parse 统计对话文件数"""
    parser = get_parser(agent_type)
    count = 0
    seen: set[str] = set()
    for base_path in search_paths:
        if not base_path.exists():
            continue
        for file_path in base_path.rglob("*"):
            if not file_path.is_file() or not parser.can_parse(file_path):
                continue
            key = str(file_path.resolve())
            if key in seen:
                continue
            seen.add(key)
            count += 1
    return count


def _find_agent_base_path(agent_type: AgentType) -> str:
    """返回该 agent 的主目录路径（字符串）"""
    paths = AGENT_KNOWN_PATHS.get(agent_type.value, [])
    for p in paths:
        if p.exists():
            return str(p)
    return str(paths[0]) if paths else ""


def detect_agents() -> list[AgentDetectionResult]:
    """检测本机已安装的 AI Agent，返回列表（含未安装的，detected=False）"""
    results: list[AgentDetectionResult] = []
    for agent_type in AgentType:
        search_paths = AGENT_KNOWN_PATHS.get(agent_type.value, [])
        installed = any(p.exists() for p in search_paths)
        base_path = _find_agent_base_path(agent_type)
        conv_count = _count_conversations(agent_type, search_paths) if installed else 0
        results.append(
            AgentDetectionResult(
                name=agent_type.value,
                detected=installed,
                path=base_path,
                conversation_count=conv_count,
            )
        )
    return results
