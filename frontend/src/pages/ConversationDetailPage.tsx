import { useParams, Link } from 'react-router-dom'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useApi } from '../hooks/useApi'
import { api } from '../api/client'
import MessageBubble from '../components/MessageBubble'
import SummaryPanel from '../components/SummaryPanel'
import LoadingSpinner from '../components/LoadingSpinner'
import { formatTokens } from '../utils/format'
import type { ConversationDetail, SummaryOut } from '../types'

export default function ConversationDetailPage() {
  const { agentName, sessionId } = useParams<{ agentName: string; sessionId: string }>()
  const { t } = useTranslation()
  const { data: conversation, loading, error } = useApi<ConversationDetail>(
    () => api.getConversation(agentName!, sessionId!),
    [agentName, sessionId],
    !!agentName && !!sessionId,
  )

  const [summarizing, setSummarizing] = useState(false)
  const [summary, setSummary] = useState<SummaryOut | null>(null)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  const handleSummarize = async () => {
    if (!agentName || !sessionId) return
    setSummarizing(true)
    setSummaryError(null)
    try {
      const result = await api.summarize(agentName, sessionId)
      setSummary(result)
    } catch (e) {
      const msg = e instanceof Error ? e.message : ''
      if (msg.includes('未配置摘要模型') || msg.includes('No summarizer configured')) {
        setSummaryError(t('detail.noProvider'))
      } else if (msg.includes('所有摘要') || msg.includes('All summarizer') || msg.includes('摘要提供者均失败')) {
        setSummaryError(t('detail.providerUnavailable'))
      } else {
        setSummaryError(t('detail.summaryFailed'))
      }
    } finally {
      setSummarizing(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/" className="hover:text-blue-600">{t('detail.home')}</Link>
        <span>/</span>
        <Link to={`/agents/${agentName}/conversations`} className="hover:text-blue-600 capitalize">
          {agentName}
        </Link>
        <span>/</span>
        <span className="text-gray-900 font-medium truncate max-w-xs">{sessionId}</span>
      </div>

      {loading && <LoadingSpinner />}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {conversation && (
        <>
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-1">{t('detail.conversation')}</h2>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>{t('detail.messages', { count: conversation.messages.length })}</span>
                <span>
                  {formatTokens(conversation.total_tokens)}{' '}
                  {t('detail.tokens')}
                </span>
                <span>{(conversation.usage_ratio * 100).toFixed(1)}{t('detail.used')}</span>
              </div>
            </div>
            <button
              onClick={handleSummarize}
              disabled={summarizing}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {summarizing ? t('detail.generating') : t('detail.generateSummary')}
            </button>
          </div>

          {/* Summary error */}
          {summaryError && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700 mb-4">
              {summaryError}
            </div>
          )}

          {/* Summary panel */}
          {summary && (
            <div className="mb-6">
              <SummaryPanel summary={summary} />
            </div>
          )}

          {/* Messages */}
          <div className="bg-gray-100 rounded-xl p-4">
            {conversation.messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
