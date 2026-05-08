"""后端共享工具函数"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from context_bridge.core import AgentType
from context_bridge.parsers import get_parser
from context_bridge.detector import AGENT_KNOWN_PATHS


def find_conversation_file(agent_name: str, session_id: str) -> Path | None:
    """在已知路径中查找指定对话文件"""
    try:
        agent_type = AgentType(agent_name)
    except ValueError:
        return None

    parser = get_parser(agent_type)
    search_paths = AGENT_KNOWN_PATHS.get(agent_name, [])

    for base_path in search_paths:
        if not base_path.exists():
            continue
        for file_path in base_path.rglob("*"):
            if not file_path.is_file():
                continue
            if parser.can_parse(file_path):
                if file_path.stem == session_id:
                    return file_path
                conv = parser.parse(file_path)
                if conv and conv.session_id == session_id:
                    return file_path
    return None
