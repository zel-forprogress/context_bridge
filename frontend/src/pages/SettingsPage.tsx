import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'
import { notifyConfigChanged } from '../hooks/useConfigSync'
import LoadingSpinner from '../components/LoadingSpinner'
import type { AppConfig, Provider } from '../types'

export default function SettingsPage() {
  const { t } = useTranslation()
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({})
  const [realKeys, setRealKeys] = useState<Record<string, string>>({})
  const [ollamaModels, setOllamaModels] = useState<string[]>(() => {
    // 从 localStorage 读取缓存
    const cached = localStorage.getItem('ollama_models')
    return cached ? JSON.parse(cached) : []
  })
  const [ollamaAvailable, setOllamaAvailable] = useState(() => {
    const cached = localStorage.getItem('ollama_available')
    return cached === 'true'
  })
  const messageTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  const loadConfig = async () => {
    try {
      const data = await api.getConfig()
      // 保留掩码 key 的显示，后端会在保存时自动保留未修改的真实 key
      setConfig(data)
      setVisibleKeys({})
      setRealKeys({})
      setLoading(false)
    } catch {
      setMessage({ type: 'error', text: t('settings.loadError') })
      setLoading(false)
    }
  }

  const loadOllamaModels = async () => {
    try {
      const data = await api.getOllamaModels()
      setOllamaModels(data.models || [])
      setOllamaAvailable(data.available)
      // 缓存到 localStorage
      localStorage.setItem('ollama_models', JSON.stringify(data.models || []))
      localStorage.setItem('ollama_available', String(data.available))
    } catch {
      setOllamaModels([])
      setOllamaAvailable(false)
      localStorage.setItem('ollama_models', '[]')
      localStorage.setItem('ollama_available', 'false')
    }
  }

  useEffect(() => {
    loadConfig()
    // 每次进入页面时在后台刷新 Ollama 模型列表
    loadOllamaModels()
  }, [])

  const toggleKeyVisibility = async (index: number) => {
    if (!config) return
    const provider = config.providers[index]
    const key = provider.name
    const isVisible = visibleKeys[key]
    if (isVisible) {
      setVisibleKeys((prev) => ({ ...prev, [key]: false }))
    } else {
      if (!realKeys[key]) {
        try {
          const data = await api.getProviderKey(provider.name)
          setRealKeys((prev) => ({ ...prev, [key]: data.api_key }))
          updateProvider(index, 'api_key', data.api_key)
        } catch {
          // 获取失败，忽略
        }
      }
      setVisibleKeys((prev) => ({ ...prev, [key]: true }))
    }
  }

  useEffect(() => {
    loadConfig()
  }, [])

  const showMessage = (msg: { type: 'success' | 'error'; text: string }) => {
    setMessage(msg)
    clearTimeout(messageTimer.current)
    if (msg.type === 'success') {
      messageTimer.current = setTimeout(() => setMessage(null), 3000)
    }
  }

  const handleSave = async () => {
    if (!config) return
    setSaving(true)
    setMessage(null)

    try {
      console.log('保存配置:', JSON.stringify(config, null, 2))
      await api.updateConfig(config)
      showMessage({ type: 'success', text: t('settings.saveSuccess') })
      const updated = { ...config }
      updated.providers = updated.providers.map((p) => ({
        ...p,
        has_key: !!p.api_key,
      }))
      setConfig(updated)
      notifyConfigChanged()
    } catch {
      showMessage({ type: 'error', text: t('settings.saveError') })
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

  const removeProvider = async (index: number) => {
    if (!config) return
    const name = config.providers[index].name || t('settings.providerName')
    if (!window.confirm(t('settings.confirmRemove', { name }))) return
    const updated = {
      ...config,
      providers: config.providers.filter((_, i) => i !== index),
    }
    setConfig(updated)
    try {
      await api.updateConfig(updated)
      showMessage({ type: 'success', text: t('settings.saveSuccess') })
    } catch {
      showMessage({ type: 'error', text: t('settings.saveFailed') })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner />
      </div>
    )
  }

  if (!config) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-red-500 mb-3">{t('settings.loadError')}</div>
          <button
            onClick={() => { setLoading(true); loadConfig() }}
            className="px-4 py-2 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
          >
            {t('settings.retry')}
          </button>
        </div>
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
                  <div className="relative">
                    <input
                      type={visibleKeys[provider.name] ? 'text' : 'password'}
                      value={provider.api_key}
                      onChange={(e) => updateProvider(index, 'api_key', e.target.value)}
                      placeholder={provider.has_key ? '' : t('settings.apiKeyPlaceholder')}
                      className="w-full px-3 py-2 pr-10 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                    />
                    {provider.has_key && (
                      <button
                        type="button"
                        onClick={() => toggleKeyVisibility(index)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-0.5"
                      >
                        {visibleKeys[provider.name] ? (
                          // 眼睛打开（可见）
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        ) : (
                          // 眼睛关闭（隐藏）
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.879L21 21" />
                          </svg>
                        )}
                      </button>
                    )}
                  </div>
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
                <div>
                  <label className="block text-xs text-gray-500 mb-1">{t('settings.apiType')}</label>
                  <select
                    value={provider.api_type || 'openai'}
                    onChange={(e) => updateProvider(index, 'api_type', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                  </select>
                </div>
                <div>
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
              <select
                value={config.local.model}
                onChange={(e) =>
                  setConfig({ ...config, local: { ...config.local, model: e.target.value } })
                }
                disabled={!ollamaAvailable || ollamaModels.length === 0}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400 disabled:bg-gray-50 disabled:text-gray-500"
              >
                {ollamaAvailable && ollamaModels.length > 0 ? (
                  <>
                    <option value="">{t('settings.selectModel')}</option>
                    {ollamaModels.map((model) => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </>
                ) : (
                  <option value="">{t('settings.noModel')}</option>
                )}
              </select>
              {!ollamaAvailable && (
                <p className="mt-2 text-xs text-amber-600">
                  {t('settings.ollamaNotRunning')}
                  <a
                    href="https://ollama.com/download"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-1 underline hover:text-amber-700"
                  >
                    {t('settings.installOllama')}
                  </a>
                </p>
              )}
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
