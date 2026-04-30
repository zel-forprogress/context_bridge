"""文件监控器 - 监控 agent 对话文件变化"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from context_bridge.config import AgentConfig
from context_bridge.core import Conversation


class ConversationFileHandler(FileSystemEventHandler):
    def __init__(self, on_change: Callable[[Path], None]):
        super().__init__()
        self._on_change = on_change
        self._debounce: dict[str, float] = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        # 只关注 jsonl / json 文件
        if path.suffix not in (".jsonl", ".json"):
            return
        # 简单防抖：同一文件 1 秒内只触发一次
        key = str(path)
        now = time.time()
        if now - self._debounce.get(key, 0) < 1.0:
            return
        self._debounce[key] = now
        self._on_change(path)


class FileWatcher:
    def __init__(self, agent_configs: dict[str, AgentConfig]):
        self._agent_configs = agent_configs
        self._observers: list[Observer] = []
        self._callbacks: list[Callable[[str, Path], None]] = []

    def on_file_changed(self, callback: Callable[[str, Path], None]):
        self._callbacks.append(callback)

    def start(self):
        for name, cfg in self._agent_configs.items():
            if not cfg.enabled:
                continue
            for path_str in cfg.paths:
                watch_dir = Path(path_str).expanduser()
                if not watch_dir.exists():
                    continue
                handler = ConversationFileHandler(
                    lambda p, n=name: self._notify(n, p)
                )
                observer = Observer()
                observer.schedule(handler, str(watch_dir), recursive=True)
                observer.start()
                self._observers.append(observer)

    def stop(self):
        for obs in self._observers:
            obs.stop()
        for obs in self._observers:
            obs.join(timeout=5)
        self._observers.clear()

    def _notify(self, agent_name: str, path: Path):
        for cb in self._callbacks:
            try:
                cb(agent_name, path)
            except Exception:
                pass  # 不让回调异常影响监控
