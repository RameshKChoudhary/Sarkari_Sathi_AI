import { useEffect, useState } from 'react'

/** Run an async loader once per dependency change; returns {data, error, loading}. */
export function useApi(loader, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  useEffect(() => {
    let alive = true
    setState((s) => ({ ...s, loading: true, error: null }))
    loader().then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((error) => alive && setState({ data: null, error, loading: false }))
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return state
}

export function useStoredState(key, initial) {
  const [v, setV] = useState(() => { try { const s = localStorage.getItem(key); return s ? JSON.parse(s) : initial } catch { return initial } })
  useEffect(() => { try { localStorage.setItem(key, JSON.stringify(v)) } catch { /* ignore */ } }, [key, v])
  return [v, setV]
}

export function useHashRoute(defaultRoute = 'chat') {
  const read = () => (window.location.hash.replace('#/', '') || defaultRoute)
  const [route, setRoute] = useState(read)
  useEffect(() => { const h = () => setRoute(read()); window.addEventListener('hashchange', h); return () => window.removeEventListener('hashchange', h) }, [])
  return [route, (r) => { window.location.hash = `#/${r}` }]
}
