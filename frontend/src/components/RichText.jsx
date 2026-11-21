import { splitCitations, toBlocks } from '../services/text.js'

function Line({ text, onCite }) {
  return splitCitations(text).map((p, i) => p.cite
    ? <button key={i} type="button" onClick={() => onCite?.(p.cite)} className="cite-chip" aria-label={`Source ${p.cite}`}>{p.cite}</button>
    : <span key={i}>{p.text.split(/\*\*(.+?)\*\*/g).map((s, j) => (j % 2 ? <strong key={j}>{s}</strong> : s))}</span>)
}

/** Renders answer/passages: headings, paragraphs, tables, bold and clickable [n] citation chips. */
export default function RichText({ text, onCite }) {
  return (
    <div className="space-y-2 leading-relaxed">
      {toBlocks(text || '').map((b, i) => {
        if (b.type === 'heading') return <h4 key={i} className="font-semibold text-slate-900">{b.text}</h4>
        if (b.type === 'table') return (
          <div key={i} className="overflow-x-auto"><table className="min-w-full border border-slate-300 text-sm">
            <tbody>{b.rows.map((r, ri) => (
              <tr key={ri} className={ri === 0 ? 'bg-slate-100 font-medium' : ''}>
                {r.cells.map((c, ci) => <td key={ci} className="border border-slate-300 px-2 py-1">{c}</td>)}
                {r.cite && <td className="px-1"><Line text={r.cite} onCite={onCite} /></td>}
              </tr>))}</tbody></table></div>)
        return <p key={i}><Line text={b.text} onCite={onCite} /></p>
      })}
    </div>
  )
}
