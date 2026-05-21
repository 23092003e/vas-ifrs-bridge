'use client'

import { useState, useEffect } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'

type SidebarState = 'expanded' | 'collapsed' | 'hidden'
type Theme = 'light' | 'dark'
type Palette = 'slate' | 'bordeaux' | 'forest' | 'graphite'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light')
  const [palette] = useState<Palette>('slate')
  const [sidebarState, setSidebarState] = useState<SidebarState>('expanded')

  useEffect(() => {
    const handler = () => setSidebarState(s => s === 'expanded' ? 'hidden' : 'expanded')
    window.addEventListener('vas-toggle-sidebar', handler)
    return () => window.removeEventListener('vas-toggle-sidebar', handler)
  }, [])

  return (
    <div
      className="app"
      data-sidebar={sidebarState}
      data-theme={theme}
      {...(palette !== 'slate' ? { 'data-palette': palette } : {})}
    >
      <Sidebar
        sidebarState={sidebarState}
        theme={theme}
        onToggleTheme={() => setTheme(t => t === 'light' ? 'dark' : 'light')}
        onNewChat={() => window.dispatchEvent(new CustomEvent('vas-new-chat'))}
      />
      <main className="main">
        {children}
      </main>
    </div>
  )
}
