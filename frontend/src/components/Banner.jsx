export default function Banner({ t, health }) {
  if (!health || health.status === 'error') return null
  const sample = (health.data_status || []).some((s) => s !== 'official')
  const offline = String(health.llm || '').startsWith('extractive')
  if (!sample && !offline) return null
  return <div className="bg-amber-50 px-4 py-1.5 text-center text-xs text-amber-900" role="note">{sample && <span>{t.bannerSample} </span>}{offline && <span>{t.bannerOffline}</span>}</div>
}
