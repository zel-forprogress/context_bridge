"""监控状态与控制接口"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas import MonitorStatus
from watcher_manager import watcher_manager

router = APIRouter()


@router.get("/monitor/status", response_model=MonitorStatus)
def get_monitor_status():
    """获取当前监控状态"""
    config = watcher_manager.config
    threshold = config.monitor.context_threshold if config else 0.85

    return MonitorStatus(
        running=watcher_manager.running,
        started_at=watcher_manager.started_at.isoformat() if watcher_manager.started_at else None,
        watched_agents=watcher_manager.watched_agents,
        context_threshold=threshold,
        summary_count=watcher_manager.summary_count,
        last_summary_time=watcher_manager.last_summary_time.isoformat() if watcher_manager.last_summary_time else None,
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
