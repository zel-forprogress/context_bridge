import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../api/client'
import AgentCard from '../components/AgentCard'
import LoadingSpinner from '../components/LoadingSpinner'
import type { AgentInfo, MonitorStatus } from '../types'

function MonitorPanel() {
  const { data: status, loading, reload } = useApi<MonitorStatus>(() => api.getMonitorStatus())
  const [actionLoading, setActionLoading] = useState(false)

  const toggleMonitor = async () => {
    if (!status) return
    setActionLoading(true)
    try {
      if (status.running) {
        await api.stopMonitor()
      } else {
        await api.startMonitor()
      }
      await reload()
    } catch (e) {
      console.error('Monitor toggle failed:', e)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <div className="bg-white rounded-xl border p-4"><LoadingSpinner /></div>

  if (!status) return null

  return (
    <div className="bg-white rounded-xl border p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900">Context Monitor</h3>
        <button
          onClick={toggleMonitor}
          disabled={actionLoading}
          className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            status.running
              ? 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200'
              : 'bg-green-50 text-green-700 hover:bg-green-100 border border-green-200'
          } disabled:opacity-50`}
        >
          {actionLoading ? '...' : status.running ? 'Stop' : 'Start'}
        </button>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span className={`inline-block w-2.5 h-2.5 rounded-full ${status.running ? 'bg-green-500' : 'bg-gray-400'}`} />
        <span className="text-sm text-gray-600">
          {status.running ? 'Monitoring' : 'Stopped'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-gray-500">Agents:</span>
          <span className="ml-1 text-gray-900">{status.watched_agents.join(', ') || 'None'}</span>
        </div>
        <div>
          <span className="text-gray-500">Threshold:</span>
          <span className="ml-1 text-gray-900">{(status.context_threshold * 100).toFixed(0)}%</span>
        </div>
        <div>
          <span className="text-gray-500">Summaries:</span>
          <span className="ml-1 text-gray-900">{status.summary_count}</span>
        </div>
        {status.last_summary_time && (
          <div>
            <span className="text-gray-500">Last:</span>
            <span className="ml-1 text-gray-900">
              {new Date(status.last_summary_time).toLocaleString()}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default function HomePage() {
  const { data: agents, loading, error } = useApi<AgentInfo[]>(() => api.getAgents())

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <MonitorPanel />
      </div>

      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Detected Agents</h2>
        <p className="text-gray-500">
          Auto-detected AI agents installed on your machine. Click an agent to browse conversations.
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
