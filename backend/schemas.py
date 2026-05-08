from pydantic import BaseModel


class AgentInfo(BaseModel):
    name: str
    detected: bool
    path: str
    conversation_count: int


class ConversationSummary(BaseModel):
    id: str
    agent: str
    file_path: str
    title: str
    message_count: int
    total_tokens: int
    max_tokens: int
    usage_ratio: float
    is_near_limit: bool
    last_activity: str | None


class MessageOut(BaseModel):
    role: str
    content: str
    timestamp: str | None
    token_count: int


class ConversationDetail(BaseModel):
    id: str
    agent: str
    file_path: str
    messages: list[MessageOut]
    total_tokens: int
    max_tokens: int
    usage_ratio: float
    is_near_limit: bool
    last_activity: str | None


class SummaryOut(BaseModel):
    id: str
    agent: str
    session_id: str
    summary: str
    key_decisions: list[str]
    pending_tasks: list[str]
    files_modified: list[str]
    created_at: str


class ResumePromptOut(BaseModel):
    prompt: str
