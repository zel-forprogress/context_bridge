import { useTranslation } from 'react-i18next'
import { useApi } from '../hooks/useApi'
import { api } from '../api/client'
import SummaryPanel from '../components/SummaryPanel'
import LoadingSpinner from '../components/LoadingSpinner'
import type { SummaryOut } from '../types'

export default function SummariesPage() {
  const { t } = useTranslation()
  const { data: summaries, loading, error } = useApi<SummaryOut[]>(() => api.getSummaries())

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('saved.title')}</h2>
        <p className="text-gray-500">
          {t('saved.desc')}
        </p>
      </div>

      {loading && <LoadingSpinner />}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {summaries && summaries.length === 0 && (
        <div className="text-center py-12 text-gray-400">{t('saved.empty')}</div>
      )}

      {summaries && summaries.length > 0 && (
        <div className="space-y-4">
          {summaries.map((s) => (
            <SummaryPanel key={s.id} summary={s} />
          ))}
        </div>
      )}
    </div>
  )
}
