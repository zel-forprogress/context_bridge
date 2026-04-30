"""Agent 对话解析器"""

from context_bridge.core import AgentType, Conversation
from context_bridge.parsers.base import BaseParser
from context_bridge.parsers.claude import ClaudeParser
from context_bridge.parsers.cline import ClineParser
from context_bridge.parsers.cursor import CursorParser

PARSERS: dict[AgentType, type[BaseParser]] = {
    AgentType.CLAUDE: ClaudeParser,
    AgentType.CURSOR: CursorParser,
    AgentType.CLINE: ClineParser,
}


def get_parser(agent_type: AgentType) -> BaseParser:
    cls = PARSERS.get(agent_type)
    if cls is None:
        raise ValueError(f"不支持的 agent 类型: {agent_type}")
    return cls()


__all__ = ["get_parser", "BaseParser", "ClaudeParser", "CursorParser", "ClineParser"]
