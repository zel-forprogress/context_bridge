"""监控状态与控制接口"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas import MonitorStatus
from context_bridge.session import SessionManager
from context_bridge.watcher_manager import watcher_manager

router = APIRouter()

_session_mgr = SessionManager()


@router.get("/monitor/status", response_model=MonitorStatus)
def get_monitor_status():
    """获取当前监控状态"""
    # 从磁盘读取实际摘要数量和最新时间
    summaries = _session_mgr.list_recent(limit=9999)
    summary_count = len(summaries)
    last_summary_time = None
    if summaries:
        last_summary_time = summaries[0].stat().st_mtime
        from datetime import datetime
        last_summary_time = datetime.fromtimestamp(last_summary_time)

    return MonitorStatus(
        running=watcher_manager.running,
        started_at=watcher_manager.started_at.isoformat() if watcher_manager.started_at else None,
        watched_agents=watcher_manager.watched_agents,
        summary_count=summary_count,
        last_summary_time=last_summary_time.isoformat() if last_summary_time else None,
    )


@router.post("/monitor/start")
def start_monitor():
    """启动监控"""
    if watcher_manager.running:
        return {"status": "already_running"}

    success = watcher_manager.start()
    if not success:
        raise HTTPException(status_code=500, detail="监控启动失败，请检查配置")
    return {"status": "started"}


@router.post("/monitor/stop")
def stop_monitor():
    """停止监控"""
    if not watcher_manager.running:
        return {"status": "already_stopped"}

    watcher_manager.stop()
    return {"status": "stopped"}
