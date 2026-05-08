export interface AgentInfo {
  name: string
  detected: boolean
  path: string
  conversation_count: number
}

export interface ConversationSummary {
  id: string
  agent: string
  file_path: string
  title: string
  message_count: number
  total_tokens: number
  max_tokens: number
  usage_ratio: number
  is_near_limit: boolean
  last_activity: string | null
}

export interface MessageOut {
  role: string
  content: string
  timestamp: string | null
  token_count: number
}

export interface ConversationDetail {
  id: string
  agent: string
  file_path: string
  messages: MessageOut[]
  total_tokens: number
  max_tokens: number
  usage_ratio: number
  is_near_limit: boolean
  last_activity: string | null
}

export interface SummaryOut {
  id: string
  agent: string
  session_id: string
  summary: string
  key_decisions: string[]
  pending_tasks: string[]
  files_modified: string[]
  created_at: string
}

export interface ResumePromptOut {
  prompt: string
}
