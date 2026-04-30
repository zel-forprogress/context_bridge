import { useNavigate } from 'react-router-dom'
import type { AgentInfo } from '../types'

const agentIcons: Record<string, string> = {
  claude: '🟣',
  cursor: '🔵',
  cline: '🟢',
}

export default function AgentCard({ agent }: { agent: AgentInfo }) {
  const navigate = useNavigate()

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
            已安装
          </span>
        ) : (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
            未检测到
          </span>
        )}
      </div>
      {agent.detected && (
        <div className="text-sm text-gray-500">
          {agent.conversation_count} 个对话
        </div>
      )}
      {!agent.detected && (
        <div className="text-xs text-gray-400">未找到 {agent.name} 安装目录</div>
      )}
    </button>
  )
}
