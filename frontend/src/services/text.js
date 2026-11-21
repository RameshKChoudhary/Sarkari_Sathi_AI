// Pure helpers (unit-tested) used by the answer and source-card components.

/** Split `text` into [{text, hl}] parts so `highlight` can be wrapped in <mark>. Whitespace-insensitive. */
export function splitHighlight(text, highlight) {
  if (!highlight) return [{ text, hl: false }]
  let idx = text.indexOf(highlight)
  let len = highlight.length
  if (idx < 0) {
    // retry ignoring whitespace differences
    const esc = highlight.trim().split(/\s+/).map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('\\s+')
    const m = new RegExp(esc).exec(text)
    if (!m) return [{ text, hl: false }]
    idx = m.index; len = m[0].length
  }
  return [
    { text: text.slice(0, idx), hl: false },
    { text: text.slice(idx, idx + len), hl: true },
    { text: text.slice(idx + len), hl: false },
  ].filter((p) => p.text)
}

/** Turn answer / passage text into blocks: {type:'heading'|'p'|'table', ...}. Handles [TABLE] blocks and markdown pipes. */
export function toBlocks(text) {
  const lines = text.split('\n')
  const blocks = []
  let rows = []
  const flush = () => { if (rows.length) { blocks.push({ type: 'table', rows }); rows = [] } }
  for (const raw of lines) {
    const line = raw.trim()
    if (!line || line === '[TABLE]' || line === '[/TABLE]') { if (!line || line.startsWith('[/')) flush(); continue }
    if (line.startsWith('|')) {
      const cite = (line.match(/\s(\[\d+\])+\s*$/) || [''])[0]
      const cells = line.replace(/\s(\[\d+\])+\s*$/, '').split('|').slice(1, -1).map((c) => c.trim())
      if (!cells.every((c) => /^-+$/.test(c))) rows.push({ cells, cite: cite.trim() })
      continue
    }
    flush()
    const h = /^\*\*(.+)\*\*$/.exec(line)
    blocks.push(h ? { type: 'heading', text: h[1] } : { type: 'p', text: line })
  }
  flush()
  return blocks
}

/** Split a line into text and citation markers: [{cite: 2}|{text}] */
export function splitCitations(line) {
  const out = []
  const re = /\[(\d+)\]/g
  let last = 0, m
  while ((m = re.exec(line))) {
    if (m.index > last) out.push({ text: line.slice(last, m.index) })
    out.push({ cite: Number(m[1]) })
    last = m.index + m[0].length
  }
  if (last < line.length) out.push({ text: line.slice(last) })
  return out
}
