import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const { t, i18n } = useTranslation()

  const navItems = [
    { path: '/', label: t('nav.agents'), icon: '🤖' },
    { path: '/summaries', label: t('nav.summaries'), icon: '📋' },
  ]

  const toggleLanguage = () => {
    const next = i18n.language === 'zh' ? 'en' : 'zh'
    i18n.changeLanguage(next)
  }

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
            const active =
              item.path === '/'
                ? location.pathname === '/' || location.pathname.startsWith('/agents') || location.pathname.startsWith('/conversations')
                : location.pathname.startsWith(item.path)
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
          <button
            onClick={toggleLanguage}
            className="w-full px-3 py-1.5 rounded-lg text-xs text-gray-500 hover:bg-gray-100 transition-colors"
          >
            {i18n.language === 'zh' ? 'English' : '中文'}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
