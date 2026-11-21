import { describe, expect, it } from 'vitest'
import { parseSSE } from './api.js'
import { splitCitations, splitHighlight, toBlocks } from './text.js'

describe('parseSSE', () => {
  it('parses complete events and keeps the remainder', () => {
    const [ev, rest] = parseSSE('event: stage\ndata: {"stage":"retrieve"}\n\nevent: token\ndata: {"te')
    expect(ev).toEqual([{ event: 'stage', data: { stage: 'retrieve' } }])
    expect(rest).toBe('event: token\ndata: {"te')
  })
  it('handles Devanagari JSON', () => {
    const [ev] = parseSSE('event: token\ndata: {"text":"नमस्ते "}\n\n')
    expect(ev[0].data.text).toBe('नमस्ते ')
  })
})

describe('splitHighlight', () => {
  it('wraps the exact match', () => {
    expect(splitHighlight('abc def ghi', 'def')).toEqual([
      { text: 'abc ', hl: false }, { text: 'def', hl: true }, { text: ' ghi', hl: false }])
  })
  it('tolerates whitespace differences and misses', () => {
    expect(splitHighlight('abc  def\nghi', 'def ghi').some((p) => p.hl)).toBe(true)
    expect(splitHighlight('abc', 'zzz')).toEqual([{ text: 'abc', hl: false }])
    expect(splitHighlight('abc', null)).toEqual([{ text: 'abc', hl: false }])
  })
})

describe('toBlocks / splitCitations', () => {
  it('builds headings, paragraphs and tables with citations', () => {
    const b = toBlocks('**Scheme — Benefits**\nPays ₹6,000. [1]\n| Category | Amount |\n|---|---|\n| Shishu | ₹50,000 | [1]')
    expect(b.map((x) => x.type)).toEqual(['heading', 'p', 'table'])
    expect(b[2].rows).toHaveLength(2)
    expect(b[2].rows[1].cite).toBe('[1]')
  })
  it('splits citation markers', () => {
    expect(splitCitations('Pays money [1][2].')).toEqual([{ text: 'Pays money ' }, { cite: 1 }, { cite: 2 }, { text: '.' }])
  })
})
