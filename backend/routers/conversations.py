"""对话详情接口"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from context_bridge.core import AgentType
from context_bridge.parsers import get_parser

from context_bridge.detector import AGENT_KNOWN_PATHS
from schemas import ConversationDetail, MessageOut

router = APIRouter()


def _find_conversation_file(agent_name: str, session_id: str) -> Path | None:
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
            if file_path.stem != session_id:
                continue
            if parser.can_parse(file_path):
                return file_path
    return None


@router.get("/conversations/{agent_name}/{session_id}", response_model=ConversationDetail)
def get_conversation(agent_name: str, session_id: str):
    """获取对话详情（含所有消息）"""
    file_path = _find_conversation_file(agent_name, session_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="对话文件未找到")

    try:
        agent_type = AgentType(agent_name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的 Agent: {agent_name}")

    parser = get_parser(agent_type)
    conv = parser.parse(file_path)
    if conv is None:
        raise HTTPException(status_code=500, detail="对话文件解析失败")

    messages = [
        MessageOut(
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp.isoformat() if msg.timestamp else None,
            token_count=msg.token_count,
        )
        for msg in conv.messages
    ]

    last_activity_str = None
    if conv.last_activity:
        last_activity_str = conv.last_activity.isoformat()

    return ConversationDetail(
        id=conv.session_id,
        agent=conv.agent.value,
        file_path=str(conv.file_path),
        messages=messages,
        total_tokens=conv.total_tokens,
        max_tokens=conv.max_tokens,
        usage_ratio=round(conv.usage_ratio, 4),
        is_near_limit=conv.is_near_limit,
        last_activity=last_activity_str,
    )
