import { useTranslation } from 'react-i18next'
import { useApi } from '../hooks/useApi'
import { api } from '../api/client'
import AgentCard from '../components/AgentCard'
import LoadingSpinner from '../components/LoadingSpinner'
import type { AgentInfo } from '../types'

export default function HomePage() {
  const { t } = useTranslation()
  const { data: agents, loading, error } = useApi<AgentInfo[]>(() => api.getAgents())

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('home.detectedAgents')}</h2>
        <p className="text-gray-500">
          {t('home.detectedDesc')}
        </p>
      </div>

      {loading && <LoadingSpinner />}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {agents && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <AgentCard key={agent.name} agent={agent} />
          ))}
        </div>
      )}
    </div>
  )
}
