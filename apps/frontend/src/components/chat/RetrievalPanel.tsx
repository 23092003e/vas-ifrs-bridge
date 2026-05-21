'use client'

import { useState } from 'react'
import type { Citation, Message } from '@/types/api'
import { MOCK_RETRIEVAL_SCORES } from '@/lib/constants'

/* ── Toggle ── */
function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <div
      role="switch"
      aria-checked={on}
      tabIndex={0}
      onKeyDown={e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); onChange(!on) } }}
      onClick={() => onChange(!on)}
      style={{
        width: 34, height: 18, borderRadius: 9,
        background: on ? 'var(--accent)' : 'var(--border-strong)',
        cursor: 'pointer', position: 'relative',
        transition: 'background 150ms ease', flexShrink: 0,
      }}
    >
      <div style={{
        position: 'absolute', top: 2, left: on ? 18 : 2,
        width: 14, height: 14, borderRadius: '50%',
        background: '#fff', boxShadow: '0 1px 2px rgba(0,0,0,0.25)',
        transition: 'left 150ms ease',
      }} />
    </div>
  )
}

/* ── Icons ── */
function CloseIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  )
}

/* ── Chunk card ── */
function ChunkCard({ citation, index }: { citation: Citation; index: number }) {
  const score = MOCK_RETRIEVAL_SCORES[index] ?? 0.55
  const page = citation.chunk_id.split('-').pop() ?? '–'
  const scoreClass = score >= 0.8 ? 'score-high' : score >= 0.6 ? 'score-mid' : 'score-low'

  return (
    <div className="chunk">
      <div className="chunk-hd">
        <div className="chunk-num">{index + 1}</div>
        <div className="chunk-doc">
          {citation.doc_id}
          <small>p.{page}</small>
        </div>
        <div className={`chunk-score ${scoreClass}`}>{score.toFixed(2)}</div>
      </div>
      <p className="chunk-excerpt">"{citation.snippet.slice(0, 100)}…"</p>
    </div>
  )
}

/* ── Settings tab ── */
function RetrievalSettings({
  topK, setTopK, threshold, setThreshold, rerank, setRerank, searchType, setSearchType,
}: {
  topK: number; setTopK: (v: number) => void
  threshold: number; setThreshold: (v: number) => void
  rerank: boolean; setRerank: (v: boolean) => void
  searchType: string; setSearchType: (v: string) => void
}) {
  const labelStyle: React.CSSProperties = { fontSize: '0.7rem', fontWeight: 500, color: 'var(--ink)', fontFamily: 'var(--font-mono)' }
  const valueStyle: React.CSSProperties = { fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent)', fontFamily: 'var(--font-mono)' }

  return (
    <div>
      <div style={{ marginBottom: 14 }}>
        <div style={{ marginBottom: 5 }}><span style={labelStyle}>Search Type</span></div>
        <select value={searchType} onChange={e => setSearchType(e.target.value)} style={{
          width: '100%', fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
          padding: '5px 22px 5px 8px', border: '1px solid var(--border)', borderRadius: 3,
          background: 'var(--surface)', color: 'var(--ink)', outline: 'none', cursor: 'pointer',
          appearance: 'none', WebkitAppearance: 'none',
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='9' height='9' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'no-repeat', backgroundPosition: 'right 6px center',
        }}>
          <option value="hybrid">Hybrid (Semantic + Keyword)</option>
          <option value="semantic">Semantic Only</option>
          <option value="keyword">Keyword Only</option>
        </select>
      </div>
      {[
        { label: 'Top-K', val: String(topK), min: 1, max: 20, step: 1, cur: topK, set: setTopK },
        { label: 'Score Threshold', val: threshold.toFixed(2), min: 0, max: 1, step: 0.01, cur: threshold, set: setThreshold },
      ].map(s => (
        <div key={s.label} style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
            <span style={labelStyle}>{s.label}</span>
            <span style={valueStyle}>{s.val}</span>
          </div>
          <input type="range" min={s.min} max={s.max} step={s.step} value={s.cur}
            onChange={e => s.set(Number(e.target.value))} style={{ width: '100%' }} />
        </div>
      ))}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={labelStyle}>Rerank</div>
          <div style={{ fontSize: '0.6rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>Cross-encoder reranker</div>
        </div>
        <Toggle on={rerank} onChange={setRerank} />
      </div>
    </div>
  )
}

/* ── Session tab ── */
function SessionInfo({ sessionId, messageCount }: { sessionId: string; messageCount: number }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(sessionId).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div>
      {[
        { label: 'Session ID', value: `${sessionId.slice(0, 8)}…`, copy: true },
        { label: 'Status', value: 'Active', copy: false },
        { label: 'Queries', value: String(messageCount), copy: false },
      ].map(r => (
        <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontSize: '0.67rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>{r.label}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ fontSize: '0.67rem', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--ink)' }}>{r.value}</span>
            {r.copy && (
              <button type="button" onClick={copy}
                style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: copied ? 'var(--success)' : 'var(--muted)', padding: 2 }}
              >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
              </button>
            )}
          </div>
        </div>
      ))}
      <button type="button" style={{
        width: '100%', marginTop: 6, padding: '6px 0',
        fontSize: '0.68rem', fontWeight: 600, fontFamily: 'var(--font-mono)',
        borderRadius: 4, border: '1px solid var(--accent)',
        background: 'var(--accent-soft)', color: 'var(--accent-ink)', cursor: 'pointer',
      }}>
        Clear Session
      </button>
    </div>
  )
}

/* ── Public ── */
export interface RetrievalPanelProps { messages: Message[]; onClose?: () => void }

export function RetrievalPanel({ messages, onClose }: RetrievalPanelProps) {
  const [tab, setTab] = useState<'chunks' | 'settings' | 'session'>('chunks')
  const [topK, setTopK] = useState(5)
  const [threshold, setThreshold] = useState(0.30)
  const [rerank, setRerank] = useState(true)
  const [searchType, setSearchType] = useState('hybrid')

  const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant' && !m.loading)
  const citations: Citation[] = lastAssistant?.citations ?? []
  const msgCount = messages.filter(m => m.role === 'user').length
  const sessionId = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'

  return (
    <aside className="drawer" data-open="true">
      <div className="drawer-hd">
        <span className="drawer-hd-title">Retrieval Inspector</span>
        <div className="drawer-hd-actions">
          <button type="button" onClick={onClose} className="topbar-iconbtn" title="Close">
            <CloseIcon />
          </button>
        </div>
      </div>

      <div className="drawer-tabs">
        {(['chunks', 'settings', 'session'] as const).map(t => (
          <button
            key={t}
            type="button"
            className="drawer-tab"
            data-active={tab === t ? 'true' : undefined}
            onClick={() => setTab(t)}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
            {t === 'chunks' && citations.length > 0 && (
              <span style={{ marginLeft: 4, color: 'var(--accent)', fontWeight: 600 }}>§{citations.length}</span>
            )}
          </button>
        ))}
      </div>

      <div className="drawer-body">
        {tab === 'chunks' && (
          citations.length === 0 ? (
            <div className="drawer-empty">
              <div className="drawer-empty-icon">◈</div>
              <p>No chunks yet. Submit a query to inspect sources.</p>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <span style={{ fontSize: '0.63rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>Top-K</span>
                <div style={{ display: 'flex', borderRadius: 3, overflow: 'hidden', border: '1px solid var(--border)' }}>
                  {[3, 5, 10].map(k => (
                    <button key={k} type="button" onClick={() => setTopK(k)} style={{
                      padding: '2px 9px', fontSize: '0.65rem', fontFamily: 'var(--font-mono)',
                      border: 'none', cursor: 'pointer',
                      background: topK === k ? 'var(--accent)' : 'transparent',
                      color: topK === k ? '#fff' : 'var(--muted)',
                    }}>
                      {k}
                    </button>
                  ))}
                </div>
              </div>
              {citations.slice(0, topK).map((c, i) => <ChunkCard key={c.key} citation={c} index={i} />)}
            </>
          )
        )}

        {tab === 'settings' && (
          <RetrievalSettings
            topK={topK} setTopK={setTopK}
            threshold={threshold} setThreshold={setThreshold}
            rerank={rerank} setRerank={setRerank}
            searchType={searchType} setSearchType={setSearchType}
          />
        )}

        {tab === 'session' && (
          <SessionInfo sessionId={sessionId} messageCount={msgCount} />
        )}
      </div>
    </aside>
  )
}
