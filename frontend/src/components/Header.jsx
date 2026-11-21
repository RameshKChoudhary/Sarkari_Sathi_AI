import { LANGS } from '../i18n.js'

export default function Header({ t, route, go, lang, setLang }) {
  return (
    <header className="sticky top-0 z-10 border-b bg-white/95 backdrop-blur">
      <div className="tricolor" />
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-3 px-4 py-2">
        <div className="mr-auto"><h1 className="text-lg font-bold text-indigo-900">SarkariSathi AI</h1><p className="text-xs text-slate-500">{t.tagline}</p></div>
        <nav className="flex gap-1" aria-label="Main">{['chat', 'schemes', 'about'].map((r) => (
          <button key={r} type="button" onClick={() => go(r)} aria-current={route === r ? 'page' : undefined}
            className={`rounded px-3 py-1 text-sm ${route === r ? 'bg-indigo-700 text-white' : 'hover:bg-slate-100'}`}>{t.nav[r]}</button>))}</nav>
        <select aria-label="Language" value={lang} onChange={(e) => setLang(e.target.value)} className="rounded border px-2 py-1 text-sm">
          {LANGS.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}</select>
      </div>
    </header>
  )
}
