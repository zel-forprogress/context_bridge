"""Watcher 管理 - 将 CLI 的 watch 功能集成到后端"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path

from context_bridge.config import AppConfig, load_config
from context_bridge.core import AgentType
from context_bridge.parsers import get_parser
from context_bridge.watcher import FileWatcher

logger = logging.getLogger("context-bridge.watcher")


class WatcherManager:
    """管理文件监控的生命周期"""

    def __init__(self):
        self._watcher: FileWatcher | None = None
        self._config: AppConfig | None = None
        self._running = False
        self._lock = threading.Lock()
        self._started_at: datetime | None = None
        self._processed: dict[str, datetime] = {}

    @property
    def running(self) -> bool:
        return self._running

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def watched_agents(self) -> list[str]:
        if not self._config:
            return []
        return [n for n, c in self._config.agents.items() if c.enabled]

    @property
    def config(self) -> AppConfig | None:
        return self._config

    def reload_config(self, config_path: Path | None = None) -> bool:
        """重新加载配置文件（不停止监控）"""
        with self._lock:
            try:
                self._config = load_config(config_path)
                logger.info("配置已重新加载")
                return True
            except Exception as e:
                logger.error(f"重新加载配置失败: {e}")
                return False

    def start(self, config_path: Path | None = None) -> bool:
        """启动监控，返回是否成功"""
        with self._lock:
            if self._running:
                return True

            try:
                self._config = load_config(config_path)
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                return False

            if not self._config.agents:
                logger.warning("没有配置任何 agent，跳过监控启动")
                return False

            def on_file_changed(agent_name: str, file_path: Path):
                self._handle_file_change(agent_name, file_path)

            self._watcher = FileWatcher(self._config.agents)
            self._watcher.on_file_changed(on_file_changed)
            self._watcher.start()

            self._running = True
            self._started_at = datetime.now()
            logger.info(f"监控已启动，监控 agent: {', '.join(self.watched_agents)}")
            return True

    def stop(self) -> bool:
        """停止监控"""
        with self._lock:
            if not self._running:
                return True

            if self._watcher:
                self._watcher.stop()
                self._watcher = None

            self._running = False
            logger.info("监控已停止")
            return True

    def _handle_file_change(
        self,
        agent_name: str,
        file_path: Path,
    ):
        now = datetime.now()
        key = str(file_path)

        # 防止重复处理
        if self._config and key in self._processed:
            if (now - self._processed[key]).seconds < self._config.monitor.interval:
                return
        self._processed[key] = now

        # 解析对话
        if not self._config:
            return

        agent_cfg = self._config.agents.get(agent_name)
        if not agent_cfg:
            return

        try:
            agent_type = AgentType(agent_cfg.type)
        except ValueError:
            return

        parser = get_parser(agent_type)
        if not parser.can_parse(file_path):
            return

        conversation = parser.parse(file_path)
        if not conversation:
            return

        usage = conversation.usage_ratio
        logger.info(f"[{agent_name}] {file_path.name} 上下文使用: {usage:.0%}")

        # 检查是否超过阈值
        if usage < self._config.monitor.context_threshold:
            return

        logger.warning(f"[{agent_name}] {file_path.name} 上下文使用率达到 {usage:.0%}，已超过阈值 {self._config.monitor.context_threshold:.0%}")
        logger.info("请在界面中手动生成摘要")


# 全局单例
watcher_manager = WatcherManager()
