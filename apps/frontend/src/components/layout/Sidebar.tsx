'use client'

import { useState } from 'react'

/* ---- Icons ---- */
function Logo() {
  return (
    <div className="flex items-center justify-center rounded-lg shrink-0" style={{ width: 32, height: 32, background: '#7c3aed' }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    </div>
  )
}

function PlusIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  )
}

function SearchIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  )
}

function ChatIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )
}

function ModelIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" />
    </svg>
  )
}

function RetrievalIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )
}

function AdvancedIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}

function DocsIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
}

function IndexIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" />
      <line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" />
    </svg>
  )
}

function VectorIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="2" /><circle cx="18" cy="18" r="2" /><circle cx="6" cy="18" r="2" /><circle cx="18" cy="6" r="2" />
      <line x1="8" y1="6" x2="16" y2="6" /><line x1="6" y1="8" x2="6" y2="16" /><line x1="8" y1="18" x2="16" y2="18" /><line x1="18" y1="8" x2="18" y2="16" />
    </svg>
  )
}

function ChunksIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
    </svg>
  )
}

function EmbedIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
    </svg>
  )
}

function SunIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  )
}

function ManageContextIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
    </svg>
  )
}

/* ---- Types ---- */
interface SidebarProps {
  onNewChat?: () => void
  isDark: boolean
  onToggleDark: () => void
  tokenCount?: number
  tokenMax?: number
  messageCount?: number
}

const HISTORY = [
  { id: '1', label: 'Hoi ve kien truc he thong', time: 'Today' },
  { id: '2', label: 'So sanh 2 phien ban API', time: 'Today' },
  { id: '3', label: 'Huong dan cai dat', time: 'Today' },
  { id: '4', label: 'Quy trinh bao mat', time: 'Yesterday' },
  { id: '5', label: 'FAQ ve san pham', time: 'Yesterday' },
]

function SidebarNavItem({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode
  label: string
  active?: boolean
  onClick?: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs font-medium text-left"
      style={{
        background: active ? 'var(--sidebar-active-bg)' : 'transparent',
        color: active ? 'var(--sidebar-active-text)' : 'var(--sidebar-text-muted)',
      }}
      onMouseEnter={e => {
        if (!active) (e.currentTarget as HTMLButtonElement).style.background = 'var(--sidebar-hover)'
      }}
      onMouseLeave={e => {
        if (!active) (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
      }}
    >
      <span style={{ opacity: active ? 1 : 0.7 }}>{icon}</span>
      {label}
    </button>
  )
}

function SectionLabel({ label }: { label: string }) {
  return (
    <p className="px-2.5 pt-3 pb-1 text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--sidebar-text-muted)', fontSize: '0.65rem' }}>
      {label}
    </p>
  )
}

export function Sidebar({ onNewChat, isDark, onToggleDark, tokenCount = 6420, tokenMax = 32000, messageCount = 8 }: SidebarProps) {
  const [activeId, setActiveId] = useState<string>('1')
  const [search, setSearch] = useState('')
  const [activeNav, setActiveNav] = useState('')

  const tokenPct = Math.round((tokenCount / tokenMax) * 100)
  const filtered = HISTORY.filter(h => h.label.toLowerCase().includes(search.toLowerCase()))

  const todayItems = filtered.filter(h => h.time === 'Today')
  const yesterdayItems = filtered.filter(h => h.time === 'Yesterday')

  return (
    <aside
      className="flex flex-col h-full select-none shrink-0"
      style={{ width: 220, background: 'var(--sidebar-bg)', borderRight: '1px solid var(--sidebar-border)' }}
    >
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 py-4" style={{ borderBottom: '1px solid var(--sidebar-border)' }}>
        <Logo />
        <div>
          <p className="text-sm font-bold leading-none" style={{ color: 'var(--sidebar-text)' }}>RAG Chatbot</p>
        </div>
      </div>

      {/* New Chat */}
      <div className="px-3 pt-3 pb-2">
        <button
          type="button"
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-semibold"
          style={{ background: '#7c3aed', color: '#ffffff' }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = '#6d28d9' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = '#7c3aed' }}
        >
          <PlusIcon />
          New Chat
          <kbd className="ml-auto opacity-60 text-xs font-mono" style={{ fontSize: '0.6rem' }}>⌘K</kbd>
        </button>
      </div>

      {/* Search */}
      <div className="px-3 pb-2">
        <div className="flex items-center gap-2 rounded-md px-2.5 py-1.5" style={{ background: 'var(--sidebar-hover)', border: '1px solid var(--sidebar-border)' }}>
          <span style={{ color: 'var(--sidebar-text-muted)' }}><SearchIcon /></span>
          <input
            type="text"
            placeholder="Search chats..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 bg-transparent outline-none text-xs"
            style={{ color: 'var(--sidebar-text)' }}
          />
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-2">

        {/* Chat History */}
        {todayItems.length > 0 && (
          <>
            <SectionLabel label="Today" />
            {todayItems.map(item => (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveId(item.id)}
                className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs text-left mb-0.5"
                style={{
                  background: activeId === item.id ? 'var(--sidebar-active-bg)' : 'transparent',
                  color: activeId === item.id ? 'var(--sidebar-active-text)' : 'var(--sidebar-text)',
                  fontWeight: activeId === item.id ? 500 : 400,
                }}
                onMouseEnter={e => {
                  if (activeId !== item.id) (e.currentTarget as HTMLButtonElement).style.background = 'var(--sidebar-hover)'
                }}
                onMouseLeave={e => {
                  if (activeId !== item.id) (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                }}
              >
                <span style={{ color: activeId === item.id ? 'var(--sidebar-active-text)' : 'var(--sidebar-text-muted)', flexShrink: 0 }}>
                  <ChatIcon />
                </span>
                <span className="truncate">{item.label}</span>
              </button>
            ))}
          </>
        )}

        {yesterdayItems.length > 0 && (
          <>
            <SectionLabel label="Yesterday" />
            {yesterdayItems.map(item => (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveId(item.id)}
                className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs text-left mb-0.5"
                style={{
                  background: activeId === item.id ? 'var(--sidebar-active-bg)' : 'transparent',
                  color: activeId === item.id ? 'var(--sidebar-active-text)' : 'var(--sidebar-text)',
                  fontWeight: activeId === item.id ? 500 : 400,
                }}
                onMouseEnter={e => {
                  if (activeId !== item.id) (e.currentTarget as HTMLButtonElement).style.background = 'var(--sidebar-hover)'
                }}
                onMouseLeave={e => {
                  if (activeId !== item.id) (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                }}
              >
                <span style={{ color: activeId === item.id ? 'var(--sidebar-active-text)' : 'var(--sidebar-text-muted)', flexShrink: 0 }}>
                  <ChatIcon />
                </span>
                <span className="truncate">{item.label}</span>
              </button>
            ))}
          </>
        )}

        {/* Context section */}
        <SectionLabel label="Context" />
        <div className="px-2.5 py-2 rounded-md mb-1" style={{ background: 'var(--sidebar-hover)' }}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium" style={{ color: 'var(--sidebar-text)' }}>Context Window</span>
          </div>
          <div className="flex items-center gap-2 mb-1">
            <div className="flex-1 rounded-full overflow-hidden" style={{ height: 4, background: 'var(--sidebar-border)' }}>
              <div
                className="h-full rounded-full"
                style={{ width: `${tokenPct}%`, background: tokenPct > 80 ? '#ef4444' : tokenPct > 60 ? '#f59e0b' : '#7c3aed' }}
              />
            </div>
          </div>
          <p className="text-xs" style={{ color: 'var(--sidebar-text-muted)' }}>
            {tokenCount.toLocaleString()} / {tokenMax.toLocaleString()} tokens
          </p>
          <div className="flex items-center justify-between mt-1">
            <p className="text-xs" style={{ color: 'var(--sidebar-text-muted)' }}>Messages: <strong style={{ color: 'var(--sidebar-text)' }}>{messageCount}</strong></p>
          </div>
          <button
            type="button"
            className="mt-2 w-full text-xs rounded-md py-1 font-medium"
            style={{ background: 'var(--sidebar-border)', color: 'var(--sidebar-text-muted)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = '#7c3aed20'; (e.currentTarget as HTMLButtonElement).style.color = '#7c3aed' }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--sidebar-border)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--sidebar-text-muted)' }}
          >
            <ManageContextIcon />
            {' '}Manage Context
          </button>
        </div>

        {/* Settings section */}
        <SectionLabel label="Settings" />
        <SidebarNavItem icon={<ModelIcon />} label="Model Settings" active={activeNav === 'model'} onClick={() => setActiveNav(activeNav === 'model' ? '' : 'model')} />
        <SidebarNavItem icon={<RetrievalIcon />} label="Retrieval Settings" active={activeNav === 'retrieval'} onClick={() => setActiveNav(activeNav === 'retrieval' ? '' : 'retrieval')} />
        <SidebarNavItem icon={<AdvancedIcon />} label="Advanced Settings" active={activeNav === 'advanced'} onClick={() => setActiveNav(activeNav === 'advanced' ? '' : 'advanced')} />

        {/* RAG Operations */}
        <SectionLabel label="RAG Operations" />
        <SidebarNavItem icon={<DocsIcon />} label="Documents" active={activeNav === 'docs'} onClick={() => setActiveNav(activeNav === 'docs' ? '' : 'docs')} />
        <SidebarNavItem icon={<IndexIcon />} label="Indexing" active={activeNav === 'indexing'} onClick={() => setActiveNav(activeNav === 'indexing' ? '' : 'indexing')} />
        <SidebarNavItem icon={<VectorIcon />} label="Vector Store" active={activeNav === 'vector'} onClick={() => setActiveNav(activeNav === 'vector' ? '' : 'vector')} />
        <SidebarNavItem icon={<ChunksIcon />} label="Chunks" active={activeNav === 'chunks'} onClick={() => setActiveNav(activeNav === 'chunks' ? '' : 'chunks')} />
        <SidebarNavItem icon={<EmbedIcon />} label="Embedding Status" active={activeNav === 'embed'} onClick={() => setActiveNav(activeNav === 'embed' ? '' : 'embed')} />
        {/* Embedding status dot */}
        <div className="px-5 -mt-0.5 mb-1 flex items-center gap-1.5">
          <span className="inline-block rounded-full" style={{ width: 6, height: 6, background: '#10b981' }} />
        </div>
      </div>

      {/* Bottom: user info + dark toggle */}
      <div className="px-3 py-3 flex items-center gap-2" style={{ borderTop: '1px solid var(--sidebar-border)' }}>
        <div className="flex items-center justify-center rounded-lg text-white text-xs font-bold shrink-0" style={{ width: 30, height: 30, background: '#7c3aed' }}>
          D
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold truncate" style={{ color: 'var(--sidebar-text)' }}>Team: Default</p>
          <p className="text-xs truncate" style={{ color: 'var(--sidebar-text-muted)' }}>Role: Admin</p>
        </div>
        <button
          type="button"
          onClick={onToggleDark}
          className="flex items-center justify-center rounded-md p-1.5"
          style={{ color: 'var(--sidebar-text-muted)' }}
          title={isDark ? 'Light mode' : 'Dark mode'}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--sidebar-hover)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--sidebar-text)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'transparent'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--sidebar-text-muted)' }}
        >
          {isDark ? <SunIcon /> : <MoonIcon />}
        </button>
      </div>
    </aside>
  )
}
