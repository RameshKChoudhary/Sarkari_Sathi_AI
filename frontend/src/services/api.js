// Thin API client. `streamChat` consumes the Server-Sent-Events endpoint with fetch (EventSource cannot POST).
const BASE = import.meta.env.VITE_API_BASE ?? ''

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status }
}

async function request(path, options) {
  let res
  try { res = await fetch(BASE + path, options) } catch { throw new ApiError('network', 0) }
  if (!res.ok) {
    let detail = res.statusText
    try { const j = await res.json(); detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail) } catch { /* keep statusText */ }
    throw new ApiError(detail, res.status)
  }
  return res
}

export const getJSON = async (path) => (await request(path)).json()
export const postJSON = async (path, body) =>
  (await request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json()

export const fetchHealth = () => getJSON('/api/health')
export const fetchSchemes = () => getJSON('/api/schemes')
export const fetchScheme = (id) => getJSON(`/api/schemes/${encodeURIComponent(id)}`)
export const fetchSuggestions = (lang) => getJSON(`/api/suggestions?lang=${lang}`)

/** Parse an SSE text buffer. Returns [events, remainder]. */
export function parseSSE(buffer) {
  const events = []
  const blocks = buffer.split('\n\n')
  const rest = blocks.pop() ?? ''
  for (const block of blocks) {
    let event = 'message'
    const data = []
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) data.push(line.slice(5).trim())
    }
    if (data.length) {
      try { events.push({ event, data: JSON.parse(data.join('\n')) }) } catch { /* ignore malformed chunk */ }
    }
  }
  return [events, rest]
}

export async function streamChat(body, onEvent, signal) {
  const res = await request('/api/chat/stream', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal,
  })
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const [events, rest] = parseSSE(buf)
    buf = rest
    events.forEach((e) => onEvent(e.event, e.data))
  }
}
