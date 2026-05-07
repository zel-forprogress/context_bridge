import { useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const { t, i18n } = useTranslation()

  // 记住最后访问的 agent 相关路径
  const lastAgentPath = useRef('/')
  if (location.pathname === '/' || location.pathname.startsWith('/agents') || location.pathname.startsWith('/conversations')) {
    lastAgentPath.current = location.pathname
  }

  const navItems = [
    { path: lastAgentPath.current, label: t('nav.agents'), icon: '🤖', match: '/' },
    { path: '/summaries', label: t('nav.summaries'), icon: '📋' },
    { path: '/settings', label: t('nav.settings'), icon: '⚙️' },
  ]

  const isZh = i18n.language === 'zh'

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-lg font-bold text-gray-900">{t('app.title')}</h1>
          <p className="text-xs text-gray-500 mt-1">{t('app.subtitle')}</p>
        </div>
        <nav className="flex-1 p-2">
          {navItems.map((item) => {
            const matchPath = item.match || item.path
            const active =
              matchPath === '/'
                ? location.pathname === '/' || location.pathname.startsWith('/agents') || location.pathname.startsWith('/conversations')
                : location.pathname.startsWith(matchPath)
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm mb-1 transition-colors ${
                  active
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
        <div className="p-3 border-t border-gray-200">
          <div className="flex items-center justify-center gap-1 text-sm">
            <button
              onClick={() => i18n.changeLanguage('zh')}
              className={`px-1.5 py-0.5 rounded transition-colors ${
                isZh ? 'font-bold text-gray-900' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              中文
            </button>
            <span className="text-gray-300">/</span>
            <button
              onClick={() => i18n.changeLanguage('en')}
              className={`px-1.5 py-0.5 rounded transition-colors ${
                !isZh ? 'font-bold text-gray-900' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              English
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
