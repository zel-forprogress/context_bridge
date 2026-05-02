"""Watcher 管理 - 将 CLI 的 watch 功能集成到后端"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path

from context_bridge.config import AppConfig, load_config
from context_bridge.core import AgentType
from context_bridge.parsers import get_parser
from context_bridge.session import SessionManager
from context_bridge.summarizer import Summarizer
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
        self._last_summary_time: datetime | None = None
        self._summary_count = 0
        self._processed: dict[str, datetime] = {}
        self._last_summary: dict[str, datetime] = {}

    @property
    def running(self) -> bool:
        return self._running

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def last_summary_time(self) -> datetime | None:
        return self._last_summary_time

    @property
    def summary_count(self) -> int:
        return self._summary_count

    @property
    def watched_agents(self) -> list[str]:
        if not self._config:
            return []
        return [n for n, c in self._config.agents.items() if c.enabled]

    @property
    def config(self) -> AppConfig | None:
        return self._config

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

            summarizer = Summarizer(self._config.providers, self._config.local)
            session_mgr = SessionManager()

            def on_file_changed(agent_name: str, file_path: Path):
                self._handle_file_change(agent_name, file_path, summarizer, session_mgr)

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
        summarizer: Summarizer,
        session_mgr: SessionManager,
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

        # 自动摘要需要用户在配置中显式开启
        if not self._config.monitor.auto_summarize:
            logger.info("自动摘要未开启，请在界面中手动生成摘要，或在配置中设置 auto_summarize = true")
            return

        # 防止短时间内重复摘要同一会话
        summary_key = f"{agent_name}:{conversation.session_id}"
        if summary_key in self._last_summary:
            if (now - self._last_summary[summary_key]).seconds < 300:
                return

        logger.info(f"自动摘要：上下文使用率达到 {usage:.0%}，开始生成摘要...")

        try:
            summary = summarizer.summarize(conversation)
            saved_path = session_mgr.save(summary)
            self._last_summary[summary_key] = now
            self._last_summary_time = now
            self._summary_count += 1

            # 生成恢复提示
            resume_prompt = session_mgr.build_resume_prompt(summary)
            prompt_path = saved_path.with_suffix(".prompt.md")
            prompt_path.write_text(resume_prompt, encoding="utf-8")

            logger.info(f"摘要已保存: {saved_path}")
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")


# 全局单例
watcher_manager = WatcherManager()
