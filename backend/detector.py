"""Agent 自动检测 — 扫描已知路径判断哪些 AI Agent 已安装"""

from __future__ import annotations

from pathlib import Path

from context_bridge.core import AgentType
from context_bridge.parsers import get_parser

from schemas import AgentInfo

AGENT_KNOWN_PATHS: dict[str, list[Path]] = {
    "claude": [
        Path.home() / ".claude",
        Path.home() / ".claude" / "projects",
    ],
    "cursor": [
        Path.home() / ".cursor",
        Path.home() / ".cursor" / "workspaceStorage",
    ],
    "cline": [
        Path.home() / ".cline",
        Path.home() / ".cline" / "data",
    ],
}


def _count_conversations(agent_type: AgentType, search_paths: list[Path]) -> int:
    """遍历目录，用对应 parser 的 can_parse 统计对话文件数"""
    parser = get_parser(agent_type)
    count = 0
    for base_path in search_paths:
        if not base_path.exists():
            continue
        for file_path in base_path.rglob("*"):
            if file_path.is_file() and parser.can_parse(file_path):
                count += 1
    return count


def _find_agent_base_path(agent_type: AgentType) -> str:
    """返回该 agent 的主目录路径（字符串）"""
    paths = AGENT_KNOWN_PATHS.get(agent_type.value, [])
    for p in paths:
        if p.exists():
            return str(p)
    return str(paths[0]) if paths else ""


def detect_agents() -> list[AgentInfo]:
    """检测本机已安装的 AI Agent，返回列表（含未安装的，detected=False）"""
    results: list[AgentInfo] = []
    for agent_type in AgentType:
        search_paths = AGENT_KNOWN_PATHS.get(agent_type.value, [])
        detected = any(p.exists() for p in search_paths)
        base_path = _find_agent_base_path(agent_type)
        conv_count = _count_conversations(agent_type, search_paths) if detected else 0
        results.append(
            AgentInfo(
                name=agent_type.value,
                detected=detected,
                path=base_path,
                conversation_count=conv_count,
            )
        )
    return results
