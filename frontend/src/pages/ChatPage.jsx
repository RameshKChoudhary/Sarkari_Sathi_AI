import { useEffect, useRef, useState } from 'react'
import Message from '../components/Message.jsx'
import { fetchSuggestions, fetchSchemes } from '../services/api.js'
import { useApi } from '../hooks/useApi.js'

export default function ChatPage({ t, lang, chat, filters, setFilters }) {
  const [text, setText] = useState('')
  const end = useRef(null)
  const sugg = useApi(() => fetchSuggestions(lang), [lang])
  const schemes = useApi(fetchSchemes, [])
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [chat.messages])
  const submit = (e) => { e?.preventDefault(); if (text.trim() && !chat.busy) { chat.send(text); setText('') } }
  const ids = filters?.scheme_ids || []
  const list = Array.isArray(schemes.data) ? schemes.data : schemes.data?.schemes || []
  const items = Array.isArray(sugg.data) ? sugg.data : sugg.data?.suggestions || []
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-4">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <label className="text-slate-600" htmlFor="sf">{t.filters}</label>
        <select id="sf" className="rounded border px-2 py-1" value={ids[0] || ''} onChange={(e) => setFilters(e.target.value ? { ...filters, scheme_ids: [e.target.value] } : omit(filters, 'scheme_ids'))}>
          <option value="">{t.allSchemes}</option>{list.map((s) => <option key={s.scheme_id} value={s.scheme_id}>{s.names?.[lang] || s.names?.en}</option>)}</select>
        <select aria-label="Level" className="rounded border px-2 py-1" value={filters?.levels?.[0] || ''} onChange={(e) => setFilters(e.target.value ? { ...filters, levels: [e.target.value] } : omit(filters, 'levels'))}>
          <option value="">{t.allLevels}</option><option value="central">{t.central}</option><option value="state">{t.state}</option></select>
        {filters && Object.keys(filters).length > 0 && <button type="button" className="text-indigo-700 underline" onClick={() => setFilters({})}>{t.clearFilters}</button>}
        {chat.messages.length > 0 && <button type="button" className="ml-auto rounded border px-2 py-1 hover:bg-slate-100" onClick={chat.clear}>{t.clear}</button>}
      </div>
      {chat.messages.length === 0 && (
        <section className="rounded-xl bg-white p-6 text-center shadow-sm"><h2 className="text-xl font-semibold">{t.emptyTitle}</h2><p className="mt-2 text-slate-600">{t.emptyBody}</p>
          {items.length > 0 && <><p className="mt-4 text-sm font-medium text-slate-500">{t.suggested}</p>
            <div className="mt-2 flex flex-wrap justify-center gap-2">{items.map((q) => <button key={q} type="button" onClick={() => chat.send(q)} className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-sm text-indigo-900 hover:bg-indigo-100">{q}</button>)}</div></>}
        </section>)}
      <div className="flex flex-col gap-4" aria-live="polite">{chat.messages.map((m) => <Message key={m.id} m={m} t={t} onRetry={chat.retry} />)}</div>
      <div ref={end} />
      <form onSubmit={submit} className="sticky bottom-0 flex gap-2 bg-slate-50 pb-3 pt-2">
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder={t.placeholder} aria-label={t.placeholder} maxLength={1000} className="min-w-0 flex-1 rounded-lg border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        {chat.busy ? <button type="button" onClick={chat.stop} className="rounded-lg bg-slate-600 px-4 text-white">{t.stop}</button>
          : <button type="submit" disabled={!text.trim()} className="rounded-lg bg-indigo-700 px-4 text-white disabled:opacity-50">{t.send}</button>}
      </form>
    </div>
  )
}
const omit = (o, k) => { const c = { ...(o || {}) }; delete c[k]; return c }
