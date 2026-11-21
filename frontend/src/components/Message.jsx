import { useState } from 'react'
import RichText from './RichText.jsx'
import SourceCard from './SourceCard.jsx'

export default function Message({ m, t, onRetry }) {
  const [active, setActive] = useState(null)
  if (m.role === 'user') return <div className="flex justify-end"><div className="max-w-[85%] rounded-2xl bg-indigo-700 px-4 py-2 text-white">{m.text}</div></div>
  const r = m.response
  const sources = r?.sources || m.sources || []
  const jump = (n) => { setActive(n); document.getElementById(`src-${n}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }
  return (
    <div className="flex flex-col gap-2">
      <div className={`max-w-[95%] rounded-2xl border px-4 py-3 ${r?.abstained ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-white'}`}>
        {m.status === 'loading' && !m.text && (
          <div className="flex items-center gap-2 text-slate-500" role="status"><span className="dot" /><span className="dot" /><span className="dot" />{t.stages[m.stage] || t.loading}</div>)}
        {m.status === 'error' && (
          <div role="alert" className="text-red-700"><strong>{t.errorTitle}</strong>: {m.error === 'backendDown' ? t.backendDown : m.error}
            {m.query && <button type="button" onClick={() => onRetry(m.id)} className="ml-3 rounded border border-red-300 px-2 py-0.5 text-sm">{t.retry}</button>}</div>)}
        {r?.abstained && <div className="mb-1 font-semibold text-amber-900">{t.abstained}</div>}
        {m.text && <RichText text={m.text} onCite={jump} />}
        {r && <p className="mt-2 border-t pt-2 text-xs text-slate-500">
          {t.detected}: {r.language}{r.romanized ? ` (${t.romanised})` : ''}
          {r.verification && <> · {t.verified}: {r.verification.kept_sentences}/{r.verification.checked_sentences} {t.sentencesKept}</>}
        </p>}
        {r?.disclaimer && <p className="mt-1 text-xs italic text-slate-500">{r.disclaimer}</p>}
      </div>
      {sources.length > 0 && (
        <details open className="max-w-[95%]"><summary className="cursor-pointer text-sm font-medium text-slate-600">{t.sources} ({sources.length})</summary>
          <div className="mt-2 grid gap-2">{sources.map((s, i) => <SourceCard key={s.id ?? i} source={s} index={i + 1} t={t} active={active === i + 1} />)}</div></details>)}
    </div>
  )
}
