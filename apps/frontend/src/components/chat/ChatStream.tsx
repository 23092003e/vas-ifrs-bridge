'use client'

import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import { useChat } from '@/lib/hooks/useChat'
import { MessageList } from './MessageList'
import { RetrievalPanel } from './RetrievalPanel'

function SendIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}

function StopIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
      <rect x="4" y="4" width="16" height="16" rx="2" />
    </svg>
  )
}

function ChevronDownIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  )
}

export default function ChatStream() {
  const { messages, loading, sendMessage, clearMessages, abort } = useChat()
  const [input, setInput] = useState('')
  const [lang, setLang] = useState<'vi' | 'en' | 'auto'>('en')
  const [scope, setScope] = useState<'shared' | 'tenant' | 'both'>('shared')
  const [model, setModel] = useState('Gemini 2.5 Flash')
  const [kb, setKb] = useState('IFRS Standards')
  const [searchMode, setSearchMode] = useState('Hybrid')
  const [focused, setFocused] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const handler = () => {
      clearMessages()
      setInput('')
      textareaRef.current?.focus()
    }
    window.addEventListener('vas-new-chat', handler)
    return () => window.removeEventListener('vas-new-chat', handler)
  }, [clearMessages])

  function handleSend() {
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    sendMessage(q, { lang, scope })
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleInput() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`
  }

  const canSend = input.trim().length > 0 && !loading
  const conversationTitle = messages.find(m => m.role === 'user')?.content.slice(0, 45) ?? 'New Chat'

  const selectStyle: React.CSSProperties = {
    border: '1px solid var(--chat-border)',
    background: 'var(--chat-surface)',
    color: 'var(--chat-text)',
    borderRadius: 6,
    fontSize: '0.75rem',
    padding: '4px 24px 4px 8px',
    outline: 'none',
    cursor: 'pointer',
    minWidth: 120,
    appearance: 'none',
    WebkitAppearance: 'none',
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 6px center',
  }

  return (
    <div style={{ display: 'flex', flex: 1, overflow: 'hidden', minWidth: 0 }}>

      {/* ── Center chat column ── */}
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden', background: 'var(--chat-bg)', minWidth: 0 }}>

        {/* Top bar */}
        <header style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 20px',
          background: 'var(--topbar-bg)',
          borderBottom: '1px solid var(--topbar-border)',
          flexShrink: 0,
          gap: 16,
          flexWrap: 'wrap',
        }}>
          {/* Title */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
            <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--chat-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }}>
              {conversationTitle}
            </span>
            <span style={{ color: 'var(--chat-text-muted)' }}><ChevronDownIcon /></span>
          </div>

          {/* Dropdowns */}
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16 }}>
            <div>
              <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--chat-text-muted)', marginBottom: 3 }}>Model</div>
              <select value={model} onChange={e => setModel(e.target.value)} style={selectStyle}>
                <option>Gemini 2.5 Flash</option>
                <option>Gemini 1.5 Pro</option>
                <option>GPT-4o-mini</option>
                <option>GPT-4o</option>
                <option>Claude 3.5 Sonnet</option>
              </select>
            </div>
            <div>
              <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--chat-text-muted)', marginBottom: 3 }}>Knowledge Base</div>
              <div style={{ display: 'flex', alignItems: 'center', position: 'relative' }}>
                <span style={{ position: 'absolute', left: 8, width: 6, height: 6, borderRadius: '50%', background: '#10b981', zIndex: 1, pointerEvents: 'none' }} />
                <select value={kb} onChange={e => setKb(e.target.value)} style={{ ...selectStyle, paddingLeft: 20 }}>
                  <option>IFRS Standards</option>
                  <option>VAS Standards</option>
                  <option>All Standards</option>
                </select>
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--chat-text-muted)', marginBottom: 3 }}>Search</div>
              <select value={searchMode} onChange={e => setSearchMode(e.target.value)} style={selectStyle}>
                <option>Hybrid</option>
                <option>Semantic</option>
                <option>Keyword</option>
              </select>
            </div>
          </div>

          {/* User avatar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 30, height: 30, borderRadius: '50%', background: '#7c3aed', color: '#fff', fontSize: '0.7rem', fontWeight: 700, flexShrink: 0 }}>
              AD
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--chat-text)', lineHeight: 1 }}>Admin</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--chat-text-muted)', marginTop: 2 }}>admin@demo.com</div>
            </div>
          </div>
        </header>

        {/* Messages */}
        <MessageList messages={messages} onSuggestion={text => { setInput(text); textareaRef.current?.focus() }} />

        {/* Input */}
        <div style={{ padding: '12px 16px 16px', background: 'var(--chat-bg)', flexShrink: 0 }}>
          <div style={{ maxWidth: 760, margin: '0 auto' }}>
            <div style={{
              background: 'var(--input-bg)',
              border: `1.5px solid ${focused ? 'var(--input-focus-border)' : 'var(--input-border)'}`,
              boxShadow: focused ? 'var(--input-focus-shadow)' : 'var(--input-shadow)',
              borderRadius: 16,
              transition: 'border-color 150ms ease, box-shadow 150ms ease',
            }}>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onInput={handleInput}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder="Ask anything about your documents..."
                rows={1}
                disabled={loading}
                style={{
                  display: 'block',
                  width: '100%',
                  resize: 'none',
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  padding: '14px 16px 8px',
                  fontSize: '0.875rem',
                  lineHeight: 1.6,
                  color: 'var(--chat-text)',
                  fontFamily: 'inherit',
                  maxHeight: 180,
                }}
              />
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 12px 10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--chat-text-muted)' }}>
                    Lang:
                  </span>
                  {(['en', 'vi', 'auto'] as const).map(l => (
                    <button
                      key={l}
                      type="button"
                      onClick={() => setLang(l)}
                      style={{
                        padding: '2px 8px',
                        borderRadius: 6,
                        fontSize: '0.7rem',
                        fontWeight: 500,
                        border: '1px solid var(--chat-border)',
                        background: lang === l ? '#7c3aed' : 'transparent',
                        color: lang === l ? '#fff' : 'var(--chat-text-muted)',
                        cursor: 'pointer',
                      }}
                    >
                      {l.toUpperCase()}
                    </button>
                  ))}
                  <span style={{ fontSize: '0.7rem', color: 'var(--chat-text-muted)', marginLeft: 8 }}>Scope:</span>
                  {(['shared', 'both'] as const).map(s => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setScope(s)}
                      style={{
                        padding: '2px 8px',
                        borderRadius: 6,
                        fontSize: '0.7rem',
                        fontWeight: 500,
                        border: '1px solid var(--chat-border)',
                        background: scope === s ? '#7c3aed' : 'transparent',
                        color: scope === s ? '#fff' : 'var(--chat-text-muted)',
                        cursor: 'pointer',
                      }}
                    >
                      {s === 'shared' ? 'Shared' : 'All'}
                    </button>
                  ))}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {loading && (
                    <button
                      type="button"
                      onClick={abort}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        padding: '6px 12px', borderRadius: 8,
                        fontSize: '0.75rem', fontWeight: 500,
                        color: '#ef4444', background: '#fef2f2',
                        border: '1px solid #fecaca', cursor: 'pointer',
                      }}
                    >
                      <StopIcon /> Stop
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={!canSend}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      width: 32, height: 32, borderRadius: 10,
                      background: canSend ? '#7c3aed' : 'var(--chat-border)',
                      color: canSend ? '#fff' : 'var(--chat-text-muted)',
                      border: 'none',
                      cursor: canSend ? 'pointer' : 'not-allowed',
                      transition: 'background 150ms ease',
                    }}
                  >
                    <SendIcon />
                  </button>
                </div>
              </div>
            </div>
            <p style={{ textAlign: 'center', fontSize: '0.7rem', color: 'var(--chat-text-muted)', marginTop: 6 }}>
              RAG Chatbot co the mac loi. Hay kiem tra thong tin quan trong.
            </p>
          </div>
        </div>
      </div>

      {/* ── Right retrieval panel ── */}
      <RetrievalPanel messages={messages} />
    </div>
  )
}
