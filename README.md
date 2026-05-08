# Context Bridge

<div align="center">

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

**AI Agent 上下文管理工具**

[下载安装包](https://github.com/zel-forprogress/context_bridge/releases/latest) | [使用文档](#使用指南) | [开发文档](#开发运行)

</div>

---

Context Bridge 是一个 AI Agent 上下文管理工具。它会读取本机 AI 编程助手的对话记录，估算上下文使用量，并在需要时生成结构化摘要，帮助你在新会话中快速接上之前的工作。

## ✨ 特性

- 🤖 **多 Agent 支持** - 自动检测 Claude Code、Codex 等 AI 编程助手
- 📊 **智能分析** - 估算对话 token 使用量，实时显示上下文使用率
- 🎯 **结构化摘要** - 自动生成包含目标、决策、任务、文件的结构化摘要
- 🌐 **多提供商支持** - 支持 OpenAI、Anthropic、DeepSeek 等云端 API，以及 Ollama 本地模型
- 🔄 **智能降级** - 云端 API 失败时自动降级到本地模型
- 📋 **一键恢复** - 生成恢复提示词，快速在新会话中恢复上下文
- 🌍 **国际化** - 支持中文和英文界面
- 🎨 **现代化界面** - 基于 React + Electron 的桌面应用

## 📥 快速开始

### Windows 用户（推荐）

1. 前往 [Releases](https://github.com/zel-forprogress/context_bridge/releases/latest) 页面
2. 下载 `Context Bridge Setup 0.1.0.exe`
3. 双击运行安装程序
4. 完成安装后启动应用

### 首次配置

1. 打开应用，点击右上角齿轮图标进入设置页面
2. 配置 LLM 提供商（至少配置一个）：
   - **云端提供商**：填写 API Key、Base URL、模型名称，选择 API 类型
   - **本地提供商**：确保 Ollama 已启动，从下拉框选择模型
3. 点击"保存配置"

## 🔧 使用 Ollama 本地模型

### 安装 Ollama

1. 访问 [https://ollama.ai](https://ollama.ai) 下载安装
2. 安装完成后，Ollama 会自动在后台运行

### 下载推荐模型

```bash
# 推荐的对话模型
ollama pull qwen2:7b
ollama pull llama3:8b
ollama pull mistral:7b

# 查看已安装的模型
ollama list
```

### 在 Context Bridge 中使用

1. 打开设置页面
2. 在"本地模型"部分，从下拉框选择已安装的模型
3. 勾选"启用本地模型"
4. 保存配置

## 📖 使用指南

### 1. 查看对话列表

- 应用会自动检测本机已安装的 AI Agent
- 点击 Agent 卡片查看该 Agent 的所有对话
- 对话列表显示会话 ID、消息数量、token 使用率等信息

### 2. 生成摘要

- 点击对话进入详情页面
- 点击"生成摘要"按钮
- 系统会调用配置的 LLM 生成结构化摘要
- 摘要包含：对话目标、关键决策、待办任务、修改文件

### 3. 复制恢复提示词

- 在对话详情页面，点击"复制恢复提示词"
- 在新的 AI Agent 会话中粘贴该提示词
- AI Agent 会快速理解之前的工作上下文

## 🎯 为什么需要它

使用 Claude Code、Codex 等 AI Agent 进行开发时，经常会遇到这些问题：

- ❌ 对话上下文快满了，需要开新会话继续工作
- ❌ 新会话缺少之前的项目背景、技术决策和待办事项
- ❌ 手动整理上下文耗时，也容易遗漏关键细节

Context Bridge 的目标是把这些上下文自动沉淀下来，让新会话可以从一份清晰的摘要继续。

## 🤖 支持的 LLM 提供商

### 云端提供商

| 提供商 | API 类型 | 说明 |
| --- | --- | --- |
| OpenAI | OpenAI | GPT-4、GPT-3.5 等模型 |
| Anthropic | Anthropic | Claude 系列模型 |
| DeepSeek | OpenAI | DeepSeek Chat 模型 |
| 通义千问 | OpenAI | Qwen 系列模型 |
| 其他 OpenAI 兼容 API | OpenAI | 任何兼容 OpenAI API 格式的服务 |

### 本地提供商

| 提供商 | 说明 |
| --- | --- |
| Ollama | 支持 Qwen、Llama、Mistral 等开源模型 |

## 📝 配置文件

配置文件位置：`C:\Users\<用户名>\.context-bridge\config.toml`

示例配置：

```toml
# 云端提供商配置
[[summarizer.providers]]
name = "Claude"
enabled = true
api_key = "sk-ant-xxx"
base_url = "https://api.anthropic.com"
model = "claude-sonnet-4-6"
api_type = "anthropic"

[[summarizer.providers]]
name = "DeepSeek"
enabled = true
api_key = "sk-xxx"
base_url = "https://api.deepseek.com"
model = "deepseek-chat"
api_type = "openai"

# 本地模型配置
[summarizer.local]
enabled = true
base_url = "http://localhost:11434"
model = "qwen2:7b"
```

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

## 🎮 支持的 AI Agent

| Agent | 状态 | 说明 |
| --- | --- | --- |
| Claude Code | ✅ 已支持 | 解析 `~/.claude/projects/` 下的 JSONL 对话文件 |
| Codex | ✅ 已支持 | 解析 `~/.codex/sessions/` 和 `~/.codex/archived_sessions/` 下的 rollout JSONL |

## 🏗️ 技术架构

- **Python 核心库**：负责配置、Agent 检测、对话解析、摘要生成和摘要保存
- **FastAPI 后端**：把核心能力包装成本地 API
- **React + Electron 前端**：提供桌面界面，用于查看 Agent、浏览对话、生成摘要和复制恢复提示词

## 🛠️ 开发运行

### 前置要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 1. 克隆项目

```bash
git clone https://github.com/zel-forprogress/context_bridge.git
cd context-bridge
```

### 2. 安装 Python 依赖

```bash
pip install -e .
pip install -r backend/requirements.txt
```

### 3. 配置文件

```bash
cp config.example.toml config.toml
# 编辑 config.toml，配置你的 LLM 提供商
```

### 4. 启动后端（可选）

如果需要单独测试后端：

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

后端健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

### 5. 启动前端开发服务（可选）

如果需要在浏览器中测试前端：

```bash
cd frontend
npm install
npm run dev
```

默认前端地址是 `http://localhost:5173`。

### 6. 启动 Electron 桌面端（推荐）

```bash
cd frontend
npm install
npm run dev:electron
```

Electron 模式会自动启动一个本地 Python 后端，并通过 IPC 将后端端口传给前端。

### 7. 打包应用

```bash
cd frontend
npm run pack    # 生成未打包的可执行文件（用于测试）
npm run dist    # 生成 NSIS 安装包
```

## 🔌 API 接口

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
| `GET` | `/api/ollama/models` | 获取 Ollama 已安装的模型列表 |

## 🔄 工作流程

1. 后端启动后加载配置文件（开发模式：`config.toml`，生产模式：`~/.context-bridge/config.toml`）
2. 系统检测 Claude Code、Cursor、Cline、Codex 的已知目录，发现对话文件
3. 用户在前端浏览对话列表，查看 token 使用率
4. 选择某个对话，手动生成结构化摘要
5. 摘要保存为 JSON，并可转换成新会话可直接使用的恢复提示词
6. 在新会话开始时粘贴恢复提示词，接上之前的工作上下文

## 📊 摘要结果

摘要会包含：

- **summary**：当前对话目标和进展
- **key_decisions**：已做出的关键技术决策
- **pending_tasks**：尚未完成的任务
- **files_modified**：对话中涉及或修改过的文件

默认保存目录：

```text
~/.context-bridge/sessions/
```

## 🔧 扩展新的 Agent

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

## ⚠️ 注意事项

- 配置文件可能包含 API Key，请勿提交到版本控制系统
- Windows 终端可能出现日志中文乱码，属于已知问题，不影响功能
- 首次启动时可能需要几秒钟初始化后端服务
- 大型对话文件（>10MB）的摘要生成可能较慢

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

感谢以下开源项目：
- [Electron](https://www.electronjs.org/)
- [React](https://react.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Ollama](https://ollama.ai/)
- [Tailwind CSS](https://tailwindcss.com/)
