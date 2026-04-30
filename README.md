# Context Bridge

AI Agent 上下文监控与自动恢复工具。当对话上下文即将耗尽时，自动生成摘要并保存，方便在新会话中恢复上下文。

## 为什么需要这个工具？

使用 AI Agent 进行代码开发时，经常会遇到：
- 对话上下文窗口耗尽，压缩失败
- 需要手动开新窗口，重新描述之前的工作
- 浪费时间重复解释项目背景和技术决策

Context Bridge 通过文件监控和智能摘要，自动保存对话上下文，让你轻松在新会话中恢复工作。

## 功能

- 监控多个 AI Agent 的对话文件（Claude Code、Cursor、Cline）
- 实时估算上下文使用率
- 超过阈值时自动生成结构化摘要
- 多云端 API 降级 + 本地模型兜底
- 保存关键决策、待办任务、已修改文件

## 安装

```bash
cd context-bridge
pip install -e .
```

## 配置

```bash
cp config.example.toml config.toml
```

编辑 `config.toml`，填入你的 API Key 和 Agent 路径。

### 配置示例

```toml
# 监控的 agent
[agents.claude]
enabled = true
type = "claude"
paths = ["~/.claude/projects/"]

# 摘要提供者（按优先级）
[[summarizer.providers]]
name = "deepseek"
enabled = true
api_key = "sk-xxx"
base_url = "https://api.deepseek.com"
model = "deepseek-chat"
priority = 1

# 本地模型兜底
[summarizer.local]
enabled = true
base_url = "http://localhost:11434"
model = "qwen2.5:7b"

# 监控行为
[monitor]
interval = 5
context_threshold = 0.85
idle_timeout = 600
```

## 使用

```bash
# 启动后台监控
context-bridge watch

# 手动摘要指定文件
context-bridge summarize claude ~/.claude/projects/xxx/conversations/yyy.jsonl

# 查看已保存的摘要
context-bridge list

# 查看恢复提示
context-bridge resume ~/.context-bridge/sessions/xxx.json
```

## 工作流程

1. `context-bridge watch` 后台运行
2. 自动监控 Agent 对话文件变化
3. 上下文使用率超过 85% 时触发摘要
4. 摘要保存到 `~/.context-bridge/sessions/`
5. 在新会话中粘贴 `.prompt.md` 文件内容即可恢复上下文

## 支持的 Agent

| Agent | 状态 | 说明 |
|-------|------|------|
| Claude Code | 已支持 | JSONL 格式，自动解析 |
| Cursor | 基础支持 | JSON 格式 |
| Cline | 基础支持 | JSON 格式 |

## 摘要提供者优先级

1. DeepSeek（便宜，性价比高）
2. OpenAI / Gemini（主流云端服务）
3. 本地 Ollama（兜底，永远可用）

## 项目结构

```
context-bridge/
├── pyproject.toml
├── config.example.toml
├── README.md
└── src/
    └── context_bridge/
        ├── __init__.py
        ├── __main__.py
        ├── cli.py          # CLI 入口
        ├── config.py       # 配置管理
        ├── core.py         # 核心数据结构
        ├── watcher.py      # 文件监控
        ├── summarizer.py   # 摘要生成
        ├── session.py      # 会话管理
        └── parsers/
            ├── base.py     # 解析器基类
            ├── claude.py   # Claude Code 解析器
            ├── cursor.py   # Cursor 解析器
            └── cline.py    # Cline 解析器
```

## 扩展

### 添加新的 Agent 支持

继承 `BaseParser` 并实现 `can_parse` 和 `parse` 方法：

```python
from context_bridge.parsers.base import BaseParser
from context_bridge.core import AgentType, Conversation

class MyAgentParser(BaseParser):
    def can_parse(self, file_path):
        return "myagent" in str(file_path)

    def parse(self, file_path):
        # 解析逻辑
        return Conversation(...)
```

然后在 `parsers/__init__.py` 中注册。

### 添加新的摘要提供者

在 `config.toml` 中添加新的 provider 配置即可，系统会自动按优先级尝试。

## License

MIT
