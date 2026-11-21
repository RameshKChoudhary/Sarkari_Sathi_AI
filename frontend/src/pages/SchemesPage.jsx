import { useState } from 'react'
import RichText from '../components/RichText.jsx'
import { fetchScheme, fetchSchemes } from '../services/api.js'
import { useApi } from '../hooks/useApi.js'

function Detail({ id, t, lang, onClose, onAsk }) {
  const { data, error, loading } = useApi(() => fetchScheme(id), [id])
  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-start gap-2"><h3 className="mr-auto text-lg font-semibold">{data?.summary?.names?.[lang] || id}</h3>
        <button type="button" onClick={onClose} className="rounded border px-2 text-sm">{t.close}</button></div>
      {loading && <p>{t.loading}</p>}{error && <p role="alert" className="text-red-700">{t.errorTitle}: {error.message}</p>}
      {data && <>
        <div className="mt-2 flex flex-wrap gap-2 text-xs"><span className="rounded bg-slate-100 px-2 py-0.5">{data.summary.level === 'central' ? t.central : t.state}</span>
          {data.summary.data_status === 'sample_fixture' && <span className="rounded bg-amber-100 px-2 py-0.5 text-amber-900">{t.sample}</span>}
          {data.summary.official_url && <a className="text-indigo-700 underline" href={data.summary.official_url} target="_blank" rel="noreferrer">{t.open}</a>}</div>
        <div className="mt-3 grid gap-3 md:grid-cols-2">{Object.entries(data.sections || {}).filter(([s]) => s !== 'overview').map(([sec, byLang]) => {
          const chunk = byLang[lang] || byLang.en || Object.values(byLang)[0]
          return chunk ? <section key={sec} className="rounded border p-3"><h4 className="mb-1 font-semibold text-indigo-900">{t.sections?.[sec] || sec}</h4><RichText text={chunk.text} /></section> : null })}</div>
        <button type="button" onClick={() => onAsk(id)} className="mt-4 rounded bg-indigo-700 px-4 py-2 text-white">{t.askAbout}</button></>}
    </div>
  )
}

export default function SchemesPage({ t, lang, onAsk }) {
  const { data, error, loading } = useApi(fetchSchemes, [])
  const [q, setQ] = useState(''); const [level, setLevel] = useState(''); const [sel, setSel] = useState(null)
  const list = (Array.isArray(data) ? data : data?.schemes || []).filter((s) =>
    (!level || s.level === level) && (!q || Object.values(s.names || {}).join(' ').toLowerCase().includes(q.toLowerCase())))
  return (
    <div className="mx-auto max-w-5xl px-4 py-4">
      <h2 className="mb-3 text-xl font-semibold">{t.schemesTitle}</h2>
      <div className="mb-3 flex flex-wrap gap-2"><input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t.search} aria-label={t.search} className="min-w-0 flex-1 rounded border px-3 py-1.5" />
        <select aria-label="Level" value={level} onChange={(e) => setLevel(e.target.value)} className="rounded border px-2"><option value="">{t.allLevels}</option><option value="central">{t.central}</option><option value="state">{t.state}</option></select></div>
      {loading && <p>{t.loading}</p>}{error && <p role="alert" className="text-red-700">{t.errorTitle}: {error.message === 'network' ? t.backendDown : error.message}</p>}
      {sel && <div className="mb-4"><Detail id={sel} t={t} lang={lang} onClose={() => setSel(null)} onAsk={onAsk} /></div>}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{list.map((s) => (
        <button key={s.scheme_id} type="button" onClick={() => setSel(s.scheme_id)} className={`rounded-xl border bg-white p-3 text-left shadow-sm hover:border-indigo-400 ${sel === s.scheme_id ? 'ring-2 ring-indigo-500' : ''}`}>
          <div className="font-semibold">{s.names?.[lang] || s.names?.en}</div>
          <div className="mt-1 text-xs text-slate-500">{s.level === 'central' ? t.central : t.state} · {s.n_chunks} chunks</div></button>))}
        {!loading && !error && list.length === 0 && <p>{t.noResults}</p>}</div>
    </div>
  )
}
