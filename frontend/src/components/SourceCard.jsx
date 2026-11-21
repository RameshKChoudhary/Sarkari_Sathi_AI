import { useState } from 'react'
import { splitHighlight } from '../services/text.js'
import RichText from './RichText.jsx'

export default function SourceCard({ source, index, t, active }) {
  const [open, setOpen] = useState(false)
  const parts = splitHighlight(source.text, source.highlight)
  const long = source.text.length > 280
  return (
    <article id={`src-${index}`} className={`rounded-lg border bg-white p-3 text-sm shadow-sm ${active ? 'ring-2 ring-saffron-500' : ''} ${source.cited ? 'border-emerald-300' : 'border-slate-200'}`}>
      <header className="flex flex-wrap items-center gap-2">
        <span className="cite-chip">{index}</span>
        <h5 className="font-semibold">{source.scheme_name}</h5>
        <span className={`rounded px-1.5 py-0.5 text-xs ${source.cited ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>{source.cited ? t.cited : t.retrieved}</span>
        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">{t.sections?.[source.section_type] || source.section_type}</span>
        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs uppercase">{source.language}</span>
      </header>
      <div className={`mt-2 text-slate-700 ${open || !long ? '' : 'line-clamp-4'}`}>
        {source.text.includes('|')
          ? <RichText text={source.text} />
          : <p className="whitespace-pre-wrap">{parts.map((p, i) => (p.hl ? <mark key={i} className="hl">{p.text}</mark> : <span key={i}>{p.text}</span>))}</p>}
      </div>
      {long && <button type="button" className="mt-1 text-xs text-indigo-700 underline" onClick={() => setOpen(!open)}>{open ? '▲' : '▼'}</button>}
      <footer className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
        {source.doc_ref && <span>{t.docRef}: {source.doc_ref}</span>}
        {source.source_url && <a className="text-indigo-700 underline" href={source.source_url} target="_blank" rel="noreferrer">{t.open}</a>}
        {source.data_status === 'sample_fixture' && <span className="rounded bg-amber-100 px-1.5 py-0.5 text-amber-900">{t.sample}</span>}
      </footer>
    </article>
  )
}
