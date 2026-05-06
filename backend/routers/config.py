"""配置管理接口"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# backend/ 目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from context_bridge.config import load_config, AppConfig, ProviderConfig, LocalConfig, MonitorConfig

router = APIRouter()

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.toml"


class ProviderUpdate(BaseModel):
    name: str
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    enabled: bool = True


class LocalUpdate(BaseModel):
    enabled: bool = True
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"


class MonitorUpdate(BaseModel):
    interval: int = 5
    context_threshold: float = 0.85
    idle_timeout: int = 600
    auto_summarize: bool = False


class ConfigUpdate(BaseModel):
    providers: list[ProviderUpdate] | None = None
    local: LocalUpdate | None = None
    monitor: MonitorUpdate | None = None


def _mask_key(key: str) -> str:
    """掩码 API Key，只显示前4位和后4位"""
    if not key or len(key) <= 8:
        return "****" if key else ""
    return f"{key[:4]}****{key[-4:]}"


@router.get("/config")
def get_config():
    """获取当前配置（API Key 掩码处理）"""
    cfg = load_config(CONFIG_PATH)

    providers = []
    for p in cfg.providers:
        providers.append({
            "name": p.name,
            "api_key": _mask_key(p.api_key),
            "has_key": bool(p.api_key),
            "base_url": p.base_url,
            "model": p.model,
            "enabled": p.enabled,
        })

    return {
        "providers": providers,
        "local": {
            "enabled": cfg.local.enabled,
            "base_url": cfg.local.base_url,
            "model": cfg.local.model,
        },
        "monitor": {
            "interval": cfg.monitor.interval,
            "context_threshold": cfg.monitor.context_threshold,
            "idle_timeout": cfg.monitor.idle_timeout,
            "auto_summarize": cfg.monitor.auto_summarize,
        },
    }


def _build_toml(cfg: AppConfig) -> str:
    """将 AppConfig 序列化为 TOML 格式字符串"""
    lines = ["# Context Bridge 配置文件\n"]

    # agents
    for name, agent in cfg.agents.items():
        lines.append(f"[agents.{name}]")
        lines.append(f"enabled = {str(agent.enabled).lower()}")
        lines.append(f'type = "{agent.type}"')
        paths_str = ", ".join(f'"{p}"' for p in agent.paths)
        lines.append(f"paths = [{paths_str}]")
        lines.append("")

    # summarizer providers
    for p in cfg.providers:
        lines.append("[[summarizer.providers]]")
        lines.append(f'name = "{p.name}"')
        lines.append(f"enabled = {str(p.enabled).lower()}")
        lines.append(f'api_key = "{p.api_key}"')
        lines.append(f'base_url = "{p.base_url}"')
        lines.append(f'model = "{p.model}"')
        lines.append("")

    # local
    lines.append("[summarizer.local]")
    lines.append(f"enabled = {str(cfg.local.enabled).lower()}")
    lines.append(f'base_url = "{cfg.local.base_url}"')
    lines.append(f'model = "{cfg.local.model}"')
    lines.append("")

    # monitor
    lines.append("[monitor]")
    lines.append(f"interval = {cfg.monitor.interval}")
    lines.append(f"context_threshold = {cfg.monitor.context_threshold}")
    lines.append(f"idle_timeout = {cfg.monitor.idle_timeout}")
    lines.append(f"auto_summarize = {str(cfg.monitor.auto_summarize).lower()}")
    lines.append("")

    return "\n".join(lines)


@router.put("/config")
def update_config(body: ConfigUpdate):
    """更新配置（写入 config.toml）"""
    cfg = load_config(CONFIG_PATH)

    if body.providers is not None:
        cfg.providers = [
            ProviderConfig(
                name=p.name,
                api_key=p.api_key,
                base_url=p.base_url,
                model=p.model,
                enabled=p.enabled,
            )
            for p in body.providers
        ]

    if body.local is not None:
        cfg.local = LocalConfig(
            enabled=body.local.enabled,
            base_url=body.local.base_url,
            model=body.local.model,
        )

    if body.monitor is not None:
        cfg.monitor = MonitorConfig(
            interval=body.monitor.interval,
            context_threshold=body.monitor.context_threshold,
            idle_timeout=body.monitor.idle_timeout,
            auto_summarize=body.monitor.auto_summarize,
        )

    toml_content = _build_toml(cfg)
    CONFIG_PATH.write_text(toml_content, encoding="utf-8")

    return {"status": "ok"}
