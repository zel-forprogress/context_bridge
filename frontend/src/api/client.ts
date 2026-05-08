import type {
  AgentInfo,
  ConversationSummary,
  ConversationDetail,
  SummaryOut,
  ResumePromptOut,
} from '../types'
import i18n from '../i18n'

let baseUrl = '/api'

// Electron 环境下，通过 IPC 获取后端端口并拼接绝对 URL
async function initBaseUrl() {
  const electronAPI = (window as any).electronAPI
  if (electronAPI?.getBackendPort) {
    const port = await electronAPI.getBackendPort()
    baseUrl = `http://127.0.0.1:${port}/api`
  }
}

const baseUrlReady = initBaseUrl()

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  await baseUrlReady
  const resp = await fetch(`${baseUrl}${path}`, options)
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || i18n.t('error.requestFailed'))
  }
  return resp.json()
}

export const api = {
  getAgents: () => request<AgentInfo[]>('/agents'),

  getConversations: (agent: string) =>
    request<ConversationSummary[]>(`/agents/${agent}/conversations`),

  getConversation: (agent: string, sessionId: string) =>
    request<ConversationDetail>(`/conversations/${agent}/${sessionId}`),

  summarize: (agent: string, sessionId: string) =>
    request<SummaryOut>(`/conversations/${agent}/${sessionId}/summarize`, {
      method: 'POST',
    }),

  getSummaries: (agent?: string) => {
    const params = agent ? `?agent=${agent}` : ''
    return request<SummaryOut[]>(`/summaries${params}`)
  },

  getResumePrompt: (filename: string) =>
    request<ResumePromptOut>(`/summaries/${filename}`),

  getConfig: () => request<any>('/config'),

  getProviderKey: (name: string) =>
    request<{ api_key: string }>(`/config/provider-key/${encodeURIComponent(name)}`),

  updateConfig: (config: any) =>
    request<any>('/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    }),
}
