"""摘要生成与查询接口"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from context_bridge.config import load_config
from context_bridge.core import AgentType
from context_bridge.parsers import get_parser
from context_bridge.session import SessionManager
from context_bridge.summarizer import Summarizer

from context_bridge.detector import AGENT_KNOWN_PATHS
from schemas import ConversationDetail, MessageOut, ResumePromptOut, SummaryOut

router = APIRouter()

# 延迟初始化，首次请求时加载
_config = None
_summarizer = None
_session_mgr = None


def _get_session_mgr():
    global _session_mgr
    if _session_mgr is None:
        _session_mgr = SessionManager()
    return _session_mgr


def _get_summarizer():
    global _summarizer, _config
    if _summarizer is None:
        # 从项目根目录加载 config.toml
        project_root = Path(__file__).resolve().parent.parent.parent
        config_path = project_root / "config.toml"
        _config = load_config(config_path)
        _summarizer = Summarizer(
            providers=_config.providers,
            local_config=_config.local,
        )
    return _summarizer


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
            if parser.can_parse(file_path):
                if file_path.stem == session_id:
                    return file_path
                conv = parser.parse(file_path)
                if conv and conv.session_id == session_id:
                    return file_path
    return None


@router.post("/conversations/{agent_name}/{session_id}/summarize", response_model=SummaryOut)
def summarize_conversation(agent_name: str, session_id: str):
    """为指定对话生成摘要"""
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

    summarizer = _get_summarizer()
    try:
        summary = summarizer.summarize(conv)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"摘要生成失败: {e}")

    session_mgr = _get_session_mgr()
    session_mgr.save(summary)

    return SummaryOut(
        id=f"{summary.agent.value}_{summary.session_id}_{summary.created_at.strftime('%Y%m%d_%H%M%S')}",
        agent=summary.agent.value,
        session_id=summary.session_id,
        summary=summary.summary,
        key_decisions=summary.key_decisions,
        pending_tasks=summary.pending_tasks,
        files_modified=summary.files_modified,
        created_at=summary.created_at.isoformat(),
    )


@router.get("/summaries", response_model=list[SummaryOut])
def list_summaries(agent: str | None = None, limit: int = 20):
    """列出已保存的摘要"""
    session_mgr = _get_session_mgr()
    agent_type = None
    if agent:
        try:
            agent_type = AgentType(agent)
        except ValueError:
            pass
    paths = session_mgr.list_recent(agent=agent_type, limit=limit)

    results: list[SummaryOut] = []
    for p in paths:
        try:
            summary = session_mgr.load(p)
            results.append(
                SummaryOut(
                    id=p.stem,
                    agent=summary.agent.value,
                    session_id=summary.session_id,
                    summary=summary.summary,
                    key_decisions=summary.key_decisions,
                    pending_tasks=summary.pending_tasks,
                    files_modified=summary.files_modified,
                    created_at=summary.created_at.isoformat(),
                )
            )
        except Exception:
            continue
    return results


@router.get("/summaries/{filename}", response_model=ResumePromptOut)
def get_resume_prompt(filename: str):
    """获取指定摘要的恢复提示"""
    session_mgr = _get_session_mgr()
    storage_dir = session_mgr.storage_dir
    file_path = storage_dir / f"{filename}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="摘要文件未找到")

    try:
        summary = session_mgr.load(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"摘要加载失败: {e}")

    prompt = session_mgr.build_resume_prompt(summary)
    return ResumePromptOut(prompt=prompt)
