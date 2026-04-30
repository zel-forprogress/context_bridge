"""配置管理"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        import json

        tomllib = None


@dataclass
class AgentConfig:
    name: str
    type: str  # claude / cursor / cline
    enabled: bool = True
    paths: list[str] = field(default_factory=list)


@dataclass
class ProviderConfig:
    name: str
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    enabled: bool = True
    priority: int = 99


@dataclass
class LocalConfig:
    enabled: bool = True
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"


@dataclass
class MonitorConfig:
    interval: int = 5
    context_threshold: float = 0.85
    idle_timeout: int = 600


@dataclass
class AppConfig:
    agents: dict[str, AgentConfig] = field(default_factory=dict)
    providers: list[ProviderConfig] = field(default_factory=list)
    local: LocalConfig = field(default_factory=LocalConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)


def _expand(path_str: str) -> Path:
    return Path(path_str).expanduser()


def load_config(config_path: Path | None = None) -> AppConfig:
    if config_path is None:
        config_path = Path("config.toml")

    if not config_path.exists():
        return _default_config()

    if tomllib is None:
        raise RuntimeError("需要安装 tomli 包来解析 TOML 配置文件")

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    cfg = AppConfig()

    # 解析 agents
    for name, agent_data in raw.get("agents", {}).items():
        cfg.agents[name] = AgentConfig(
            name=name,
            type=agent_data.get("type", name),
            enabled=agent_data.get("enabled", True),
            paths=agent_data.get("paths", []),
        )

    # 解析 providers
    for p in raw.get("summarizer", {}).get("providers", []):
        cfg.providers.append(
            ProviderConfig(
                name=p["name"],
                api_key=p.get("api_key", ""),
                base_url=p.get("base_url", ""),
                model=p.get("model", ""),
                enabled=p.get("enabled", True),
                priority=p.get("priority", 99),
            )
        )
    cfg.providers.sort(key=lambda x: x.priority)

    # 解析 local
    local_data = raw.get("summarizer", {}).get("local", {})
    cfg.local = LocalConfig(
        enabled=local_data.get("enabled", True),
        base_url=local_data.get("base_url", "http://localhost:11434"),
        model=local_data.get("model", "qwen2.5:7b"),
    )

    # 解析 monitor
    mon_data = raw.get("monitor", {})
    cfg.monitor = MonitorConfig(
        interval=mon_data.get("interval", 5),
        context_threshold=mon_data.get("context_threshold", 0.85),
        idle_timeout=mon_data.get("idle_timeout", 600),
    )

    return cfg


def _default_config() -> AppConfig:
    return AppConfig(
        agents={
            "claude": AgentConfig(
                name="claude",
                type="claude",
                paths=["~/.claude/projects/"],
            ),
        },
        providers=[],
        local=LocalConfig(enabled=True),
        monitor=MonitorConfig(),
    )
