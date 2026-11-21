import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, streamChat } from '../services/api.js'

const KEY = 'sarkari-chat-v1'
let nextId = Date.now()

function load() {
  try { const v = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(v) ? v.filter((m) => m.status !== 'loading') : [] } catch { return [] }
}

/** Chat state + streaming. Messages: {id, role:'user'|'assistant', text, status:'loading'|'done'|'error', stage, response, error}. */
export function useChat({ uiLanguage, filters }) {
  const [messages, setMessages] = useState(load)
  const abortRef = useRef(null)

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(messages.slice(-30))) } catch { /* storage unavailable */ }
  }, [messages])

  const patch = (id, fn) => setMessages((ms) => ms.map((m) => (m.id === id ? { ...m, ...fn(m) } : m)))

  const send = useCallback(async (query) => {
    const q = query.trim()
    if (!q) return
    const uid = ++nextId, aid = ++nextId
    setMessages((ms) => [...ms, { id: uid, role: 'user', text: q }, { id: aid, role: 'assistant', text: '', status: 'loading', stage: null, query: q }])
    const ctrl = new AbortController()
    abortRef.current = ctrl
    const body = { query: q, ui_language: uiLanguage, top_k: 5, filters: filters && Object.keys(filters).length ? filters : null }
    try {
      await streamChat(body, (event, data) => {
        if (event === 'stage') patch(aid, () => ({ stage: data.stage }))
        else if (event === 'sources') patch(aid, () => ({ sources: data }))
        else if (event === 'token') patch(aid, (m) => ({ text: m.text + data.text }))
        else if (event === 'done') patch(aid, () => ({ status: 'done', response: data, text: data.answer }))
        else if (event === 'error') patch(aid, () => ({ status: 'error', error: data.detail }))
      }, ctrl.signal)
      patch(aid, (m) => (m.status === 'loading' ? { status: 'error', error: 'stream ended early' } : {}))
    } catch (e) {
      if (e.name === 'AbortError') patch(aid, (m) => ({ status: m.text ? 'done' : 'error', error: m.text ? undefined : 'cancelled' }))
      else patch(aid, () => ({ status: 'error', error: e instanceof ApiError && e.status === 0 ? 'backendDown' : e.message }))
    } finally { abortRef.current = null }
  }, [uiLanguage, filters])

  const stop = useCallback(() => abortRef.current?.abort(), [])
  const clear = useCallback(() => { abortRef.current?.abort(); setMessages([]) }, [])
  const retry = useCallback((assistantId) => {
    const m = messages.find((x) => x.id === assistantId)
    if (m?.query) { setMessages((ms) => ms.filter((x) => x.id !== assistantId && x.id !== assistantId - 1)); send(m.query) }
  }, [messages, send])

  return { messages, send, stop, clear, retry, busy: messages.some((m) => m.status === 'loading') }
}
