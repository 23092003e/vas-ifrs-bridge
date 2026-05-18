'use client'

import { useEffect, useRef, useState } from 'react'
import type { Message, Citation } from '@/types/api'

/* ---- Icons ---- */
function BotIcon() {
  return (
    <div className="flex items-center justify-center rounded-full" style={{ width: 28, height: 28, background: '#7c3aed', flexShrink: 0 }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        <circle cx="9" cy="16" r="1" fill="white" /><circle cx="15" cy="16" r="1" fill="white" />
      </svg>
    </div>
  )
}

function CopyIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  )
}

function ThumbUpIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z" />
      <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
    </svg>
  )
}

function ThumbDownIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z" />
      <path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
    </svg>
  )
}

function ShareIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
    </svg>
  )
}

function RegenerateIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  )
}

function DocIcon({ type }: { type: string }) {
  const color = type === 'pdf' ? '#ef4444' : type === 'docx' ? '#3b82f6' : type === 'md' ? '#10b981' : '#6b7280'
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
}

function ExternalLinkIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  )
}

/* ---- Suggestion cards (empty state) ---- */
const SUGGESTIONS = [
  { title: 'IFRS 1 First-time Adoption', body: 'What are the key requirements when adopting IFRS for the first time?' },
  { title: 'Revenue Recognition', body: 'Compare VAS 15 and IFRS 15 on revenue from contracts with customers' },
  { title: 'Share-based Payments', body: 'Explain the accounting treatment under IFRS 2 for equity-settled awards' },
  { title: 'Financial Instruments', body: 'How does IFRS 9 classify and measure financial assets?' },
]

function SuggestionCard({ title, body, onClick }: { title: string; body: string; onClick: () => void }) {
  const [hovered, setHovered] = useState(false)
  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="text-left rounded-xl p-4"
      style={{
        border: `1px solid ${hovered ? '#7c3aed40' : 'var(--chat-border)'}`,
        background: hovered ? '#7c3aed08' : 'var(--chat-surface)',
        transition: 'all 150ms ease',
      }}
    >
      <p className="text-sm font-semibold mb-1" style={{ color: 'var(--chat-text)' }}>{title}</p>
      <p className="text-xs leading-relaxed" style={{ color: 'var(--chat-text-muted)' }}>{body}</p>
    </button>
  )
}

function EmptyState({ onSuggestion }: { onSuggestion: (text: string) => void }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-8 py-16">
      <div className="flex items-center justify-center rounded-2xl mb-5" style={{ width: 52, height: 52, background: '#7c3aed' }}>
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          <line x1="9" y1="7" x2="15" y2="7" /><line x1="9" y1="11" x2="15" y2="11" /><line x1="9" y1="15" x2="12" y2="15" />
        </svg>
      </div>
      <h1 className="text-xl font-bold mb-2" style={{ color: 'var(--chat-text)' }}>VAS·IFRS Knowledge Engine</h1>
      <p className="text-sm mb-8 text-center max-w-sm leading-relaxed" style={{ color: 'var(--chat-text-muted)' }}>
        Ask anything about Vietnamese Accounting Standards or IFRS. Answers grounded in retrieved documents with citations.
      </p>
      <div className="grid grid-cols-2 gap-3 w-full max-w-[580px]">
        {SUGGESTIONS.map(s => (
          <SuggestionCard key={s.title} title={s.title} body={s.body} onClick={() => onSuggestion(s.body)} />
        ))}
      </div>
    </div>
  )
}

/* ---- Source row ---- */
function SourceRow({ citation, index }: { citation: Citation; index: number }) {
  const [hovered, setHovered] = useState(false)
  const ext = citation.doc_id.split('.').pop()?.toLowerCase() ?? 'pdf'
  const scores = [0.92, 0.87, 0.78, 0.71, 0.68]
  const score = scores[index] ?? 0.60
  const scoreClass = score >= 0.8 ? 'score-high' : score >= 0.6 ? 'score-mid' : 'score-low'
  const page = citation.chunk_id.split('-').pop() ?? '–'

  return (
    <div
      className="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer"
      style={{
        border: `1px solid ${hovered ? '#7c3aed30' : 'var(--chat-border)'}`,
        background: hovered ? '#7c3aed05' : 'var(--chat-surface)',
        transition: 'all 120ms ease',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Number */}
      <span
        className="flex items-center justify-center rounded-full text-xs font-bold shrink-0"
        style={{ width: 22, height: 22, background: '#7c3aed', color: 'white' }}
      >
        {index + 1}
      </span>

      {/* Doc icon */}
      <DocIcon type={ext} />

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold truncate" style={{ color: 'var(--chat-text)' }}>{citation.doc_id}</span>
          <span className="text-xs shrink-0" style={{ color: 'var(--chat-text-muted)' }}>Trang {page}</span>
        </div>
        <p className="text-xs truncate mt-0.5" style={{ color: 'var(--chat-text-muted)' }}>
          ...{citation.snippet.slice(0, 60)}...
        </p>
      </div>

      {/* Score */}
      <span className={`text-xs font-semibold tabular-nums shrink-0 ${scoreClass}`}>{score.toFixed(2)}</span>

      {/* External link */}
      <span style={{ color: 'var(--chat-text-muted)', opacity: hovered ? 1 : 0, transition: 'opacity 120ms' }}>
        <ExternalLinkIcon />
      </span>
    </div>
  )
}

/* ---- Sources section below assistant message ---- */
function SourcesSection({ citations }: { citations: Citation[] }) {
  const [expanded, setExpanded] = useState(false)
  if (citations.length === 0) return null

  return (
    <div className="mt-4">
      <div className="flex items-center gap-2 mb-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--chat-text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
        <span className="text-xs font-semibold" style={{ color: 'var(--chat-text)' }}>Sources</span>
        <span className="text-xs" style={{ color: 'var(--chat-text-muted)' }}>{citations.length}</span>
      </div>
      <div className="space-y-1.5">
        {citations.slice(0, expanded ? undefined : 3).map((c, i) => (
          <SourceRow key={c.key} citation={c} index={i} />
        ))}
      </div>
      {citations.length > 3 && (
        <button
          type="button"
          onClick={() => setExpanded(v => !v)}
          className="mt-2 text-xs font-medium"
          style={{ color: '#7c3aed' }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.textDecoration = 'underline' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.textDecoration = 'none' }}
        >
          {expanded ? 'Show less' : `View all ${citations.length} sources`}
        </button>
      )}
    </div>
  )
}

/* ---- Message metadata badges ---- */
function MetaBadges({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null
  const trustLevel = citations.length >= 3 ? 'Cao' : citations.length >= 1 ? 'Trung binh' : 'Thap'
  const trustColor = trustLevel === 'Cao' ? '#059669' : trustLevel === 'Trung binh' ? '#d97706' : '#dc2626'
  const trustBg = trustLevel === 'Cao' ? '#f0fdf4' : trustLevel === 'Trung binh' ? '#fffbeb' : '#fef2f2'

  return (
    <div className="flex items-center gap-2 mt-2 flex-wrap">
      <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full" style={{ background: 'var(--chat-bg)', border: '1px solid var(--chat-border)', color: 'var(--chat-text-muted)' }}>
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
        </svg>
        Sources {citations.length}
      </span>
      <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full" style={{ background: trustBg, border: `1px solid ${trustColor}40`, color: trustColor }}>
        Do tin cay: {trustLevel}
      </span>
      <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full" style={{ background: 'var(--chat-bg)', border: '1px solid var(--chat-border)', color: 'var(--chat-text-muted)' }}>
        Tokens: –
      </span>
    </div>
  )
}

/* ---- Action buttons below message ---- */
function MessageActions() {
  return (
    <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
      {[
        { icon: <CopyIcon />, title: 'Copy' },
        { icon: <ThumbUpIcon />, title: 'Good response' },
        { icon: <ThumbDownIcon />, title: 'Bad response' },
        { icon: <ShareIcon />, title: 'Share' },
        { icon: <RegenerateIcon />, title: 'Regenerate' },
      ].map(({ icon, title }) => (
        <button
          key={title}
          type="button"
          title={title}
          className="flex items-center justify-center rounded-md p-1.5"
          style={{ color: 'var(--chat-text-muted)' }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--chat-text)'; (e.currentTarget as HTMLButtonElement).style.background = 'var(--chat-border)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--chat-text-muted)'; (e.currentTarget as HTMLButtonElement).style.background = 'transparent' }}
        >
          {icon}
        </button>
      ))}
    </div>
  )
}

/* ---- Single message bubble ---- */
function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'
  const isStreaming = msg.loading && msg.content.length > 0

  if (isUser) {
    return (
      <div className="flex justify-end mb-6">
        <div
          className="rounded-2xl px-4 py-3 text-sm leading-relaxed max-w-[75%]"
          style={{ background: 'var(--user-bubble-bg)', color: 'var(--user-bubble-text)', wordBreak: 'break-word' }}
        >
          <div className="flex items-center gap-2 mb-1.5 opacity-70">
            <div className="flex items-center justify-center rounded-full text-white text-xs font-bold" style={{ width: 20, height: 20, background: 'rgba(255,255,255,0.2)' }}>
              U
            </div>
            <span className="text-xs">You</span>
          </div>
          <span className="whitespace-pre-wrap">{msg.content}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3 mb-6 group">
      <BotIcon />
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-semibold" style={{ color: 'var(--chat-text)' }}>RAG Bot</span>
        </div>

        {/* Content */}
        <div className="prose-chat" style={{ wordBreak: 'break-word' }}>
          {msg.loading && !msg.content ? (
            <span className="inline-flex gap-1 items-center">
              {[0, 1, 2].map(i => (
                <span
                  key={i}
                  className="dot-bounce rounded-full"
                  style={{ width: 6, height: 6, background: 'var(--chat-text-muted)', display: 'inline-block', animationDelay: `${i * 0.2}s` }}
                />
              ))}
            </span>
          ) : (
            <span className="whitespace-pre-wrap">
              {msg.content}
              {isStreaming && <span className="cursor-blink ml-0.5">&#9611;</span>}
            </span>
          )}
        </div>

        {/* Metadata badges */}
        {!msg.loading && <MetaBadges citations={msg.citations} />}

        {/* Action buttons */}
        {!msg.loading && <MessageActions />}

        {/* Sources */}
        {!msg.loading && <SourcesSection citations={msg.citations} />}
      </div>
    </div>
  )
}

/* ---- Public ---- */
interface MessageListProps {
  messages: Message[]
  onSuggestion?: (text: string) => void
}

export function MessageList({ messages, onSuggestion }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return <EmptyState onSuggestion={onSuggestion ?? (() => {})} />
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-[760px] px-6 py-8">
        {messages.map(msg => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
