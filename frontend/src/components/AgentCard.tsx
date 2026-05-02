import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { AgentInfo } from '../types'

const agentIcons: Record<string, string> = {
  claude: '🟣',
  cursor: '🔵',
  cline: '🟢',
}

export default function AgentCard({ agent }: { agent: AgentInfo }) {
  const navigate = useNavigate()
  const { t } = useTranslation()

  return (
    <button
      onClick={() => agent.detected && navigate(`/agents/${agent.name}/conversations`)}
      disabled={!agent.detected}
      className={`w-full text-left p-5 rounded-xl border transition-all ${
        agent.detected
          ? 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md cursor-pointer'
          : 'bg-gray-50 border-gray-100 opacity-50 cursor-not-allowed'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{agentIcons[agent.name] || '⚪'}</span>
          <h3 className="text-base font-semibold text-gray-900 capitalize">
            {agent.name}
          </h3>
        </div>
        {agent.detected ? (
          <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">
            {t('agent.installed')}
          </span>
        ) : (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
            {t('agent.notDetected')}
          </span>
        )}
      </div>
      {agent.detected && (
        <div className="text-sm text-gray-500">
          {t('agent.conversations', { count: agent.conversation_count })}
        </div>
      )}
      {!agent.detected && (
        <div className="text-xs text-gray-400">{t('agent.notFound', { name: agent.name })}</div>
      )}
    </button>
  )
}
