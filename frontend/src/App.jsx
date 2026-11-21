import { useState } from 'react'
import { T } from './i18n.js'
import Header from './components/Header.jsx'
import Banner from './components/Banner.jsx'
import ChatPage from './pages/ChatPage.jsx'
import SchemesPage from './pages/SchemesPage.jsx'
import AboutPage from './pages/AboutPage.jsx'
import { useChat } from './hooks/useChat.js'
import { useApi, useHashRoute, useStoredState } from './hooks/useApi.js'
import { fetchHealth } from './services/api.js'

export default function App() {
  const [route, go] = useHashRoute('chat')
  const [lang, setLang] = useStoredState('sarkari-lang', 'en')
  const [filters, setFilters] = useState({})
  const t = { ...T.en, ...T[lang], sections: { ...T.en.sections, ...T[lang]?.sections }, stages: { ...T.en.stages, ...T[lang]?.stages }, nav: { ...T.en.nav, ...T[lang]?.nav } }
  const chat = useChat({ uiLanguage: lang, filters })
  const health = useApi(fetchHealth, [])
  const ask = (id) => { setFilters({ scheme_ids: [id] }); go('chat') }
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <Header t={t} route={route} go={go} lang={lang} setLang={setLang} />
      <Banner t={t} health={health.data} />
      <main>
        {route === 'schemes' ? <SchemesPage t={t} lang={lang} onAsk={ask} />
          : route === 'about' ? <AboutPage />
          : <ChatPage t={t} lang={lang} chat={chat} filters={filters} setFilters={setFilters} />}
      </main>
    </div>
  )
}
