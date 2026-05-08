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
from utils import find_conversation_file
from schemas import ResumePromptOut, SummaryOut

router = APIRouter()

# 配置文件路径：开发模式用项目根目录，打包模式用用户主目录
def _get_config_path() -> Path:
    dev_path = Path(__file__).resolve().parent.parent.parent / "config.toml"
    if dev_path.exists():
        return dev_path
    # 打包模式：使用用户主目录
    user_config_dir = Path.home() / ".context-bridge"
    user_config_dir.mkdir(parents=True, exist_ok=True)
    user_config_path = user_config_dir / "config.toml"
    # 如果配置文件不存在，创建默认配置
    if not user_config_path.exists():
        default_config = """# Context Bridge 配置文件

[summarizer.local]
enabled = false
base_url = "http://localhost:11434"
model = ""
"""
        user_config_path.write_text(default_config, encoding="utf-8")
    return user_config_path

CONFIG_PATH = _get_config_path()
_session_mgr = None


def _get_session_mgr():
    global _session_mgr
    if _session_mgr is None:
        _session_mgr = SessionManager()
    return _session_mgr


def _get_summarizer():
    """每次调用都从 config.toml 读取最新配置"""
    cfg = load_config(CONFIG_PATH)
    return Summarizer(providers=cfg.providers, local_config=cfg.local)


@router.post("/conversations/{agent_name}/{session_id}/summarize", response_model=SummaryOut)
def summarize_conversation(agent_name: str, session_id: str):
    """为指定对话生成摘要"""
    file_path = find_conversation_file(agent_name, session_id)
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
    if not summarizer.has_providers:
        summarizer.close()
        raise HTTPException(
            status_code=400,
            detail="未配置摘要模型。请先在设置页面配置云端或本地 LLM 提供商。",
        )
    try:
        summary = summarizer.summarize(conv)
    except Exception as e:
        msg = str(e)
        if "所有摘要提供者均失败" in msg or "所有" in msg and "失败" in msg:
            raise HTTPException(
                status_code=500,
                detail="所有摘要模型均不可用。请检查设置中的提供商配置，或确认本地 Ollama 已启动。",
            )
        raise HTTPException(status_code=500, detail=f"摘要生成失败: {e}")
    finally:
        summarizer.close()

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
