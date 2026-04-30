"""Agent 检测与对话列表接口"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

# backend/ 目录加入 sys.path，以便导入 context_bridge
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from context_bridge.core import AgentType
from context_bridge.parsers import get_parser

from detector import AGENT_KNOWN_PATHS, detect_agents
from schemas import AgentInfo, ConversationSummary

router = APIRouter()


@router.get("/agents", response_model=list[AgentInfo])
def list_agents():
    """检测本机已安装的 AI Agent"""
    return detect_agents()


@router.get("/agents/{agent_name}/conversations", response_model=list[ConversationSummary])
def list_conversations(agent_name: str):
    """列出指定 Agent 的所有对话"""
    try:
        agent_type = AgentType(agent_name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的 Agent: {agent_name}")

    parser = get_parser(agent_type)
    search_paths = AGENT_KNOWN_PATHS.get(agent_name, [])

    conversations: list[ConversationSummary] = []
    seen: set[str] = set()

    for base_path in search_paths:
        if not base_path.exists():
            continue
        for file_path in base_path.rglob("*"):
            if not file_path.is_file():
                continue
            if not parser.can_parse(file_path):
                continue
            # 去重（多个搜索路径可能重叠）
            key = str(file_path)
            if key in seen:
                continue
            seen.add(key)

            conv = parser.parse(file_path)
            if conv is None:
                continue

            last_activity_str = None
            if conv.last_activity:
                last_activity_str = conv.last_activity.isoformat()

            conversations.append(
                ConversationSummary(
                    id=conv.session_id,
                    agent=conv.agent.value,
                    file_path=str(conv.file_path),
                    message_count=len(conv.messages),
                    total_tokens=conv.total_tokens,
                    max_tokens=conv.max_tokens,
                    usage_ratio=round(conv.usage_ratio, 4),
                    is_near_limit=conv.is_near_limit,
                    last_activity=last_activity_str,
                )
            )

    # 按最后活动时间倒序
    conversations.sort(key=lambda c: c.last_activity or "", reverse=True)
    return conversations
