import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'VAS·IFRS Knowledge Engine',
  description: 'AI-powered accounting standards assistant for VAS and IFRS',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={inter.variable}>
      <body className={`${inter.className} antialiased`} style={{ height: '100%', margin: 0, overflow: 'hidden' }}>{children}</body>
    </html>
  )
}
