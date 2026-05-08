"""配置管理接口"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# backend/ 目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from context_bridge.config import load_config, AppConfig, ProviderConfig, LocalConfig

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


class ConfigUpdate(BaseModel):
    providers: list[ProviderUpdate] | None = None
    local: LocalUpdate | None = None


def _mask_key(key: str) -> str:
    """掩码 API Key，只显示前4位和后4位"""
    if not key or len(key) <= 8:
        return "****" if key else ""
    return f"{key[:4]}****{key[-4:]}"


@router.get("/config")
def get_config():
    """获取当前配置"""
    cfg = load_config(CONFIG_PATH)

    providers = []
    for p in cfg.providers:
        providers.append({
            "name": p.name,
            "api_key": p.api_key,
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

    return "\n".join(lines)


@router.get("/config/provider-key/{provider_name}")
def get_provider_key(provider_name: str):
    """获取指定 provider 的真实 API Key（用于前端眼睛按钮）"""
    cfg = load_config(CONFIG_PATH)
    for p in cfg.providers:
        if p.name == provider_name:
            return {"api_key": p.api_key}
    raise HTTPException(status_code=404, detail="Provider 未找到")


@router.put("/config")
def update_config(body: ConfigUpdate):
    """更新配置（写入 config.toml）"""
    cfg = load_config(CONFIG_PATH)

    if body.providers is not None:
        # 构建旧 provider 的 name -> api_key 映射，用于保留未修改的 key
        old_keys = {p.name: p.api_key for p in cfg.providers}
        new_providers = []
        for p in body.providers:
            api_key = p.api_key
            # 如果前端发回的是掩码 key（含 ****）或空字符串，保留原值
            if ("****" in api_key or not api_key) and p.name in old_keys and old_keys[p.name]:
                api_key = old_keys[p.name]
            new_providers.append(
                ProviderConfig(
                    name=p.name,
                    api_key=api_key,
                    base_url=p.base_url,
                    model=p.model,
                    enabled=p.enabled,
                )
            )
        cfg.providers = new_providers

    if body.local is not None:
        cfg.local = LocalConfig(
            enabled=body.local.enabled,
            base_url=body.local.base_url,
            model=body.local.model,
        )

    toml_content = _build_toml(cfg)
    CONFIG_PATH.write_text(toml_content, encoding="utf-8")

    return {"status": "ok"}
