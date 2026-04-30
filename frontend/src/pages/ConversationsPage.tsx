import { useParams, Link } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { api } from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'
import type { ConversationSummary } from '../types'

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

function UsageBar({ ratio }: { ratio: number }) {
  const percent = Math.min(ratio * 100, 100)
  let color = 'bg-green-500'
  if (percent > 85) color = 'bg-red-500'
  else if (percent > 70) color = 'bg-yellow-500'

  return (
    <div className="w-full bg-gray-200 rounded-full h-1.5">
      <div
        className={`${color} h-1.5 rounded-full transition-all`}
        style={{ width: `${percent}%` }}
      />
    </div>
  )
}

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}h ago`
  const diffD = Math.floor(diffH / 24)
  if (diffD < 7) return `${diffD}d ago`
  return d.toLocaleDateString()
}

export default function ConversationsPage() {
  const { agentName } = useParams<{ agentName: string }>()
  const { data: conversations, loading, error } = useApi<ConversationSummary[]>(
    () => api.getConversations(agentName!),
    [agentName],
  )

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/" className="hover:text-blue-600">Home</Link>
        <span>/</span>
        <span className="text-gray-900 font-medium capitalize">{agentName}</span>
      </div>

      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 capitalize mb-1">
          {agentName} Conversations
        </h2>
        <p className="text-gray-500">
          {conversations ? `${conversations.length} conversations found` : 'Loading...'}
        </p>
      </div>

      {loading && <LoadingSpinner />}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {conversations && conversations.length === 0 && (
        <div className="text-center py-12 text-gray-400">No conversations found</div>
      )}

      {conversations && conversations.length > 0 && (
        <div className="space-y-2">
          {conversations.map((conv) => (
            <Link
              key={conv.id}
              to={`/conversations/${conv.agent}/${conv.id}`}
              className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-900 truncate max-w-md">
                  {conv.id}
                </h3>
                <span className="text-xs text-gray-400">
                  {formatDate(conv.last_activity)}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>{conv.message_count} messages</span>
                <span>{formatTokens(conv.total_tokens)} / {formatTokens(conv.max_tokens)} tokens</span>
                {conv.is_near_limit && (
                  <span className="text-red-600 font-medium">Near limit!</span>
                )}
              </div>
              <div className="mt-2">
                <UsageBar ratio={conv.usage_ratio} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
