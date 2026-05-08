# Context Bridge

Context Bridge 是一个 AI Agent 上下文管理工具。它会读取本机 AI 编程助手的对话记录，估算上下文使用量，并在需要时生成结构化摘要，帮助你在新会话中快速接上之前的工作。

当前项目形态是：

- Python 核心库：负责配置、Agent 检测、对话解析、摘要生成和摘要保存。
- FastAPI 后端：把核心能力包装成本地 API。
- React + Electron 前端：提供桌面界面，用于查看 Agent、浏览对话、生成摘要和复制恢复提示词。

## 为什么需要它

使用 Claude Code、Codex 等 AI Agent 进行开发时，经常会遇到这些问题：

- 对话上下文快满了，需要开新会话继续工作。
- 新会话缺少之前的项目背景、技术决策和待办事项。
- 手动整理上下文耗时，也容易遗漏关键细节。

Context Bridge 的目标是把这些上下文自动沉淀下来，让新会话可以从一份清晰的摘要继续。

## 功能

- 检测本机已安装或已产生对话记录的 AI Agent（Claude Code、Codex）。
- 解析对话文件，估算消息 token 数和上下文使用率。
- 手动生成结构化摘要（summary、key_decisions、pending_tasks、files_modified）。
- 支持多个云端 LLM provider 按顺序降级，支持本地 Ollama 兜底。
- 将摘要保存到本地，生成可复制到新会话的恢复提示词。
- 提供 Electron 桌面界面。

## 项目结构

```text
context-bridge/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # API 入口
│   ├── schemas.py              # API 响应模型
│   ├── utils.py                # 共享工具函数
│   └── routers/
│       ├── agents.py           # Agent 检测与对话列表
│       ├── conversations.py    # 对话详情
│       ├── config.py           # 配置读写
│       └── summaries.py        # 摘要生成、列表、恢复提示词
├── frontend/                   # React + Electron 前端
│   ├── electron/               # Electron 主进程与 Python 后端管理
│   └── src/
│       ├── pages/              # 页面组件
│       ├── components/         # 通用组件
│       ├── api/                # API 客户端
│       ├── hooks/              # 自定义 hooks
│       ├── types/              # TypeScript 类型定义
│       ├── utils/              # 工具函数
│       └── i18n/               # 国际化
├── src/context_bridge/         # Python 核心库
│   ├── config.py               # 配置加载
│   ├── core.py                 # 核心数据结构
│   ├── detector.py             # Agent 自动检测
│   ├── session.py              # 摘要保存与恢复提示词生成
│   ├── summarizer.py           # LLM 摘要生成与降级
│   └── parsers/                # Agent 对话解析器
│       ├── base.py             # 基类与共享工具
│       ├── claude.py           # Claude Code 解析器
│       └── codex.py            # Codex 解析器
├── config.example.toml         # 配置模板
├── config.toml                 # 本地配置，不应提交
└── pyproject.toml              # Python 包配置
```

## 支持的 Agent

| Agent | 状态 | 说明 |
| --- | --- | --- |
| Claude Code | 已支持 | 解析 `~/.claude/projects/` 下的 JSONL 对话文件 |
| Codex | 已支持 | 解析 `~/.codex/sessions/` 和 `~/.codex/archived_sessions/` 下的 rollout JSONL |

## 配置

先从模板复制配置文件：

```bash
cp config.example.toml config.toml
```

然后编辑 `config.toml`，配置摘要模型：

```toml
[[summarizer.providers]]
name = "deepseek"
enabled = true
api_key = "sk-xxx"
base_url = "https://api.deepseek.com"
model = "deepseek-chat"

[summarizer.local]
enabled = true
base_url = "http://localhost:11434"
model = "qwen2.5:7b"
```

说明：

- 云端 provider 会按配置顺序尝试，全部失败后再使用本地 Ollama。
- Agent 的扫描路径由代码内置（`detector.py`），无需在配置文件中指定。

## 开发运行

### 1. 安装 Python 依赖

```bash
pip install -e .
pip install -r backend/requirements.txt
```

### 2. 启动 FastAPI 后端

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

后端健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

### 3. 启动前端开发服务

```bash
cd frontend
npm install
npm run dev
```

默认前端地址是 `http://localhost:5173`。

### 4. 启动 Electron 桌面端

```bash
cd frontend
npm run dev:electron
```

Electron 模式会自动启动一个本地 Python 后端，并通过 IPC 将后端端口传给前端。

## 常用 API

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/agents` | 检测本机 Agent |
| `GET` | `/api/agents/{agent}/conversations` | 获取指定 Agent 的对话列表 |
| `GET` | `/api/conversations/{agent}/{session_id}` | 获取对话详情 |
| `POST` | `/api/conversations/{agent}/{session_id}/summarize` | 为指定对话生成摘要 |
| `GET` | `/api/summaries` | 查看已保存摘要 |
| `GET` | `/api/summaries/{filename}` | 获取恢复提示词 |
| `GET` | `/api/config` | 获取配置 |
| `PUT` | `/api/config` | 更新配置 |

## 工作流程

1. 后端启动后加载 `config.toml`。
2. 系统检测 Claude Code、Codex 的已知目录，发现对话文件。
3. 用户在前端浏览对话列表，查看 token 使用率。
4. 选择某个对话，手动生成结构化摘要。
5. 摘要保存为 JSON，并可转换成新会话可直接使用的恢复提示词。
6. 在新会话开始时粘贴恢复提示词，接上之前的工作上下文。

## 摘要结果

摘要会包含：

- 当前对话目标和进展。
- 已做出的关键技术决策。
- 尚未完成的任务。
- 对话中涉及或修改过的文件。

默认保存目录：

```text
~/.context-bridge/sessions/
```

## 扩展新的 Agent

新增 Agent 支持时，需要实现一个新的 parser：

```python
from pathlib import Path

from context_bridge.core import Conversation
from context_bridge.parsers.base import BaseParser


class MyAgentParser(BaseParser):
    def can_parse(self, file_path: Path) -> bool:
        return "myagent" in str(file_path).lower()

    def parse(self, file_path: Path) -> Conversation | None:
        # 读取并解析对话文件，返回统一的 Conversation 对象
        ...
```

然后在 `src/context_bridge/parsers/__init__.py` 中注册到 `PARSERS`。

## 当前注意事项

- `config.toml` 可能包含 API Key，应保持本地使用，不要提交。
- Windows 终端可能出现日志中文乱码，属于已知问题，不影响功能。
- 如需添加新的 LLM 提供商，可通过前端设置页面或直接编辑 `config.toml`。

## License

MIT
