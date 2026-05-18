'use client'

import { useState, useEffect } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    const root = document.documentElement
    if (isDark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [isDark])

  return (
    <div
      className="flex h-screen overflow-hidden"
      style={{ background: 'var(--chat-bg)', color: 'var(--chat-text)' }}
    >
      <Sidebar
        isDark={isDark}
        onToggleDark={() => setIsDark(d => !d)}
        onNewChat={() => {
          window.dispatchEvent(new CustomEvent('vas-new-chat'))
        }}
      />
      <main className="flex flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  )
}
