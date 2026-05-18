'use client'

import { useState } from 'react'
import type { Citation, Message } from '@/types/api'

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
      style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 150ms ease', flexShrink: 0 }}
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  )
}

function DocIcon({ ext }: { ext: string }) {
  const color = ext === 'pdf' ? '#ef4444' : ext === 'docx' ? '#3b82f6' : '#6b7280'
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
}

function CopyIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  )
}

/* ── Simple inline toggle ── */
function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <div
      onClick={() => onChange(!on)}
      style={{
        position: 'relative',
        width: 36,
        height: 20,
        borderRadius: 10,
        background: on ? '#7c3aed' : '#d1d5db',
        cursor: 'pointer',
        transition: 'background 150ms ease',
        flexShrink: 0,
      }}
    >
      <div style={{
        position: 'absolute',
        top: 2,
        left: on ? 18 : 2,
        width: 16,
        height: 16,
        borderRadius: '50%',
        background: '#fff',
        boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        transition: 'left 150ms ease',
      }} />
    </div>
  )
}

/* ── Score color ── */
function scoreColor(score: number) {
  return score >= 0.8 ? '#059669' : score >= 0.6 ? '#d97706' : '#dc2626'
}

/* ── Section with collapse ── */
function Section({ title, children, defaultOpen = true }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div style={{ borderBottom: '1px solid var(--panel-border)' }}>
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          width: '100%', padding: '10px 16px',
          background: 'transparent', border: 'none', cursor: 'pointer',
        }}
      >
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--chat-text)' }}>{title}</span>
        <span style={{ color: 'var(--chat-text-muted)' }}><ChevronIcon open={open} /></span>
      </button>
      {open && <div style={{ padding: '0 16px 16px' }}>{children}</div>}
    </div>
  )
}

/* ── Chunk row ── */
function ChunkRow({ citation, index }: { citation: Citation; index: number }) {
  const [hovered, setHovered] = useState(false)
  const ext = citation.doc_id.split('.').pop()?.toLowerCase() ?? 'pdf'
  const scores = [0.92, 0.87, 0.78, 0.71, 0.68, 0.62, 0.58]
  const score = scores[index] ?? 0.55
  const page = citation.chunk_id.split('-').pop() ?? '–'

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        borderRadius: 8,
        padding: '10px',
        marginBottom: 8,
        cursor: 'pointer',
        border: `1px solid ${hovered ? '#7c3aed40' : 'var(--panel-border)'}`,
        background: hovered ? '#7c3aed08' : 'var(--chat-bg)',
        transition: 'all 120ms ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0, flex: 1 }}>
          <DocIcon ext={ext} />
          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--chat-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {citation.doc_id}
          </span>
        </div>
        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: scoreColor(score), flexShrink: 0, marginLeft: 6 }}>
          {score.toFixed(2)}
        </span>
      </div>
      <div style={{ fontSize: '0.65rem', color: 'var(--chat-text-muted)', marginBottom: 4 }}>Trang {page}</div>
      <div style={{ fontSize: '0.65rem', color: 'var(--chat-text-muted)', lineHeight: 1.5, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
        ...{citation.snippet.slice(0, 80)}...
      </div>
    </div>
  )
}

/* ── Retrieval settings ── */
function RetrievalSettings({
  topK, setTopK,
  threshold, setThreshold,
  rerank, setRerank,
  searchType, setSearchType,
}: {
  topK: number; setTopK: (v: number) => void
  threshold: number; setThreshold: (v: number) => void
  rerank: boolean; setRerank: (v: boolean) => void
  searchType: string; setSearchType: (v: string) => void
}) {
  const labelStyle: React.CSSProperties = { fontSize: '0.75rem', fontWeight: 500, color: 'var(--chat-text)' }
  const valueStyle: React.CSSProperties = { fontSize: '0.75rem', fontWeight: 600, color: '#7c3aed' }
  const rowStyle: React.CSSProperties = { marginBottom: 14 }

  return (
    <div>
      <div style={rowStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={labelStyle}>Search Type</span>
        </div>
        <select
          value={searchType}
          onChange={e => setSearchType(e.target.value)}
          style={{
            width: '100%', fontSize: '0.75rem', padding: '5px 24px 5px 8px',
            border: '1px solid var(--panel-border)', borderRadius: 6,
            background: 'var(--chat-bg)', color: 'var(--chat-text)', outline: 'none', cursor: 'pointer',
            appearance: 'none', WebkitAppearance: 'none',
            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`,
            backgroundRepeat: 'no-repeat', backgroundPosition: 'right 6px center',
          }}
        >
          <option value="hybrid">Hybrid (Semantic + Keyword)</option>
          <option value="semantic">Semantic Only</option>
          <option value="keyword">Keyword Only</option>
        </select>
      </div>

      <div style={rowStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={labelStyle}>Top-K</span>
          <span style={valueStyle}>{topK}</span>
        </div>
        <input type="range" min={1} max={20} step={1} value={topK} onChange={e => setTopK(Number(e.target.value))}
          style={{ width: '100%', accentColor: '#7c3aed' }} />
      </div>

      <div style={rowStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={labelStyle}>Score Threshold</span>
          <span style={valueStyle}>{threshold.toFixed(2)}</span>
        </div>
        <input type="range" min={0} max={1} step={0.01} value={threshold} onChange={e => setThreshold(Number(e.target.value))}
          style={{ width: '100%', accentColor: '#7c3aed' }} />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={labelStyle}>Rerank Results</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--chat-text-muted)' }}>Use cross-encoder reranker</div>
        </div>
        <Toggle on={rerank} onChange={setRerank} />
      </div>
    </div>
  )
}

/* ── Session info ── */
function SessionInfo({ sessionId, messageCount }: { sessionId: string; messageCount: number }) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(sessionId).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const rowStyle: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }
  const labelStyle: React.CSSProperties = { fontSize: '0.7rem', color: 'var(--chat-text-muted)' }
  const valueStyle: React.CSSProperties = { fontSize: '0.7rem', color: 'var(--chat-text)', fontWeight: 500 }

  return (
    <div>
      <div style={rowStyle}>
        <span style={labelStyle}>Session ID</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ ...valueStyle, fontFamily: 'monospace' }}>{sessionId.slice(0, 8)}...</span>
          <button type="button" onClick={copy} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: copied ? '#059669' : 'var(--chat-text-muted)', padding: 2 }}>
            <CopyIcon />
          </button>
        </div>
      </div>
      <div style={rowStyle}>
        <span style={labelStyle}>Created</span>
        <span style={valueStyle}>This session</span>
      </div>
      <div style={rowStyle}>
        <span style={labelStyle}>Messages</span>
        <span style={{ ...valueStyle, color: '#7c3aed', fontWeight: 700 }}>{messageCount}</span>
      </div>
      <button
        type="button"
        style={{
          width: '100%', marginTop: 8, padding: '7px 0',
          fontSize: '0.75rem', fontWeight: 500,
          color: '#ef4444', background: 'transparent',
          border: '1px solid #fecaca', borderRadius: 8, cursor: 'pointer',
        }}
        onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = '#fef2f2' }}
        onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'transparent' }}
      >
        Clear Session
      </button>
    </div>
  )
}

/* ── Public ── */
export interface RetrievalPanelProps {
  messages: Message[]
}

export function RetrievalPanel({ messages }: RetrievalPanelProps) {
  const [topK, setTopK] = useState(5)
  const [threshold, setThreshold] = useState(0.30)
  const [rerank, setRerank] = useState(true)
  const [searchType, setSearchType] = useState('hybrid')

  const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant' && !m.loading)
  const citations: Citation[] = lastAssistant?.citations ?? []
  const msgCount = messages.filter(m => m.role === 'user').length
  const sessionId = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'

  return (
    <aside style={{
      width: 280,
      flexShrink: 0,
      background: 'var(--panel-bg)',
      borderLeft: '1px solid var(--panel-border)',
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <Section title="Retrieved Chunks" defaultOpen={true}>
        {citations.length === 0 ? (
          <p style={{ fontSize: '0.75rem', color: 'var(--chat-text-muted)' }}>
            No chunks retrieved yet. Ask a question to see sources.
          </p>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--chat-text-muted)' }}>Top-K</span>
              <div style={{ display: 'flex', borderRadius: 6, overflow: 'hidden', border: '1px solid var(--panel-border)' }}>
                {[3, 5, 10].map(k => (
                  <button key={k} type="button" onClick={() => setTopK(k)} style={{
                    padding: '2px 8px', fontSize: '0.7rem', border: 'none', cursor: 'pointer',
                    background: topK === k ? '#7c3aed' : 'transparent',
                    color: topK === k ? '#fff' : 'var(--chat-text-muted)',
                  }}>
                    {k}
                  </button>
                ))}
              </div>
            </div>
            {citations.slice(0, topK).map((c, i) => (
              <ChunkRow key={c.key} citation={c} index={i} />
            ))}
            {citations.length > topK && (
              <button type="button" style={{
                width: '100%', padding: '6px 0', fontSize: '0.75rem', fontWeight: 500,
                color: '#7c3aed', background: '#7c3aed10', border: 'none', borderRadius: 8, cursor: 'pointer',
              }}>
                View all chunks &rarr;
              </button>
            )}
          </>
        )}
      </Section>

      <Section title="Retrieval Settings" defaultOpen={true}>
        <RetrievalSettings
          topK={topK} setTopK={setTopK}
          threshold={threshold} setThreshold={setThreshold}
          rerank={rerank} setRerank={setRerank}
          searchType={searchType} setSearchType={setSearchType}
        />
      </Section>

      <Section title="Session Info" defaultOpen={true}>
        <SessionInfo sessionId={sessionId} messageCount={msgCount} />
      </Section>
    </aside>
  )
}
