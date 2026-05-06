import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'
import { notifyConfigChanged } from '../hooks/useConfigSync'

interface Provider {
  name: string
  api_key: string
  has_key: boolean
  base_url: string
  model: string
  enabled: boolean
}

interface LocalConfig {
  enabled: boolean
  base_url: string
  model: string
}

interface MonitorConfig {
  interval: number
  context_threshold: number
  auto_summarize: boolean
}

interface Config {
  providers: Provider[]
  local: LocalConfig
  monitor: MonitorConfig
}

export default function SettingsPage() {
  const { t } = useTranslation()
  const [config, setConfig] = useState<Config | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const loadConfig = async () => {
    try {
      const data = await api.getConfig()
      setConfig(data)
      setLoading(false)
    } catch {
      setMessage({ type: 'error', text: t('settings.loadError') })
      setLoading(false)
    }
  }

  useEffect(() => {
    loadConfig()
  }, [])

  const handleSave = async () => {
    if (!config) return
    setSaving(true)
    setMessage(null)

    try {
      await api.updateConfig(config)
      setMessage({ type: 'success', text: t('settings.saveSuccess') })
      // 重新加载配置以获取掩码后的 key
      await loadConfig()
      // 通知其他组件配置已变更
      notifyConfigChanged()
    } catch {
      setMessage({ type: 'error', text: t('settings.saveError') })
    } finally {
      setSaving(false)
    }
  }

  const updateProvider = (index: number, field: keyof Provider, value: string | boolean) => {
    if (!config) return
    const newProviders = [...config.providers]
    newProviders[index] = { ...newProviders[index], [field]: value }
    setConfig({ ...config, providers: newProviders })
  }

  const addProvider = () => {
    if (!config) return
    setConfig({
      ...config,
      providers: [
        ...config.providers,
        { name: '', api_key: '', has_key: false, base_url: '', model: '', enabled: true },
      ],
    })
  }

  const removeProvider = (index: number) => {
    if (!config) return
    setConfig({
      ...config,
      providers: config.providers.filter((_, i) => i !== index),
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">{t('common.loading')}</div>
      </div>
    )
  }

  if (!config) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500">{t('settings.loadError')}</div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('settings.title')}</h1>

      {message && (
        <div
          className={`mb-4 p-3 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* LLM Providers */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">{t('settings.providers')}</h2>
          <button
            onClick={addProvider}
            className="px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
          >
            + {t('settings.addProvider')}
          </button>
        </div>

        <div className="space-y-4">
          {config.providers.map((provider, index) => (
            <div key={index} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <input
                  type="text"
                  value={provider.name}
                  onChange={(e) => updateProvider(index, 'name', e.target.value)}
                  placeholder={t('settings.providerName')}
                  className="text-base font-medium text-gray-900 bg-transparent border-none outline-none placeholder-gray-400"
                />
                <div className="flex items-center gap-2">
                  <label className="flex items-center gap-1.5 text-sm text-gray-600">
                    <input
                      type="checkbox"
                      checked={provider.enabled}
                      onChange={(e) => updateProvider(index, 'enabled', e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    {t('settings.enabled')}
                  </label>
                  <button
                    onClick={() => removeProvider(index)}
                    className="text-red-400 hover:text-red-600 text-sm"
                  >
                    {t('settings.remove')}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">{t('settings.apiKey')}</label>
                  <input
                    type="password"
                    value={provider.api_key}
                    onChange={(e) => updateProvider(index, 'api_key', e.target.value)}
                    placeholder={provider.has_key ? '••••••••' : t('settings.apiKeyPlaceholder')}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">{t('settings.baseUrl')}</label>
                  <input
                    type="text"
                    value={provider.base_url}
                    onChange={(e) => updateProvider(index, 'base_url', e.target.value)}
                    placeholder="https://api.example.com"
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">{t('settings.model')}</label>
                  <input
                    type="text"
                    value={provider.model}
                    onChange={(e) => updateProvider(index, 'model', e.target.value)}
                    placeholder="gpt-4o-mini"
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Local Model */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">{t('settings.localModel')}</h2>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-base font-medium text-gray-900">Ollama</span>
            <label className="flex items-center gap-1.5 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={config.local.enabled}
                onChange={(e) =>
                  setConfig({ ...config, local: { ...config.local, enabled: e.target.checked } })
                }
                className="rounded border-gray-300"
              />
              {t('settings.enabled')}
            </label>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">{t('settings.baseUrl')}</label>
              <input
                type="text"
                value={config.local.base_url}
                onChange={(e) =>
                  setConfig({ ...config, local: { ...config.local, base_url: e.target.value } })
                }
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">{t('settings.model')}</label>
              <input
                type="text"
                value={config.local.model}
                onChange={(e) =>
                  setConfig({ ...config, local: { ...config.local, model: e.target.value } })
                }
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Monitor Settings */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">{t('settings.monitor')}</h2>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">{t('settings.interval')}</label>
              <input
                type="number"
                value={config.monitor.interval}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    monitor: { ...config.monitor, interval: Number(e.target.value) },
                  })
                }
                min="1"
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                {t('settings.contextThreshold')}
              </label>
              <input
                type="number"
                value={config.monitor.context_threshold}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    monitor: { ...config.monitor, context_threshold: Number(e.target.value) },
                  })
                }
                min="0"
                max="1"
                step="0.05"
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
              />
            </div>
            <div className="flex items-center">
              <label className="flex items-center gap-1.5 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={config.monitor.auto_summarize}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      monitor: { ...config.monitor, auto_summarize: e.target.checked },
                    })
                  }
                  className="rounded border-gray-300"
                />
                {t('settings.autoSummarize')}
              </label>
            </div>
          </div>
        </div>
      </section>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? t('settings.saving') : t('settings.save')}
        </button>
      </div>
    </div>
  )
}
