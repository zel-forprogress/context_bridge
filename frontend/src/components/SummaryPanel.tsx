import { useState } from 'react'
import type { SummaryOut } from '../types'
import { api } from '../api/client'

export default function SummaryPanel({ summary }: { summary: SummaryOut }) {
  const [prompt, setPrompt] = useState<string | null>(null)
  const [copying, setCopying] = useState(false)

  const handleCopyPrompt = async () => {
    setCopying(true)
    try {
      if (!prompt) {
        const result = await api.getResumePrompt(summary.id)
        setPrompt(result.prompt)
      }
      await navigator.clipboard.writeText(prompt || '')
    } catch (e) {
      console.error('Failed to copy:', e)
    } finally {
      setCopying(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-900">Summary</h3>
        <button
          onClick={handleCopyPrompt}
          disabled={copying}
          className="text-xs px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors disabled:opacity-50"
        >
          {copying ? 'Copying...' : 'Copy Resume Prompt'}
        </button>
      </div>

      <div className="text-sm text-gray-700 mb-4 leading-relaxed">{summary.summary}</div>

      {summary.key_decisions.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">
            Key Decisions
          </h4>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-0.5">
            {summary.key_decisions.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        </div>
      )}

      {summary.pending_tasks.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">
            Pending Tasks
          </h4>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-0.5">
            {summary.pending_tasks.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      )}

      {summary.files_modified.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">
            Files Modified
          </h4>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-0.5 font-mono">
            {summary.files_modified.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="text-xs text-gray-400 mt-3">
        Created: {new Date(summary.created_at).toLocaleString()}
      </div>
    </div>
  )
}
