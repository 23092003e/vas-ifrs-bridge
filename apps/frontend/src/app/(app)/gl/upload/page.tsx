'use client'

export default function GlUploadPage() {
  return (
    <div style={{ flex: 1, overflow: 'auto', background: 'var(--chat-bg)' }}>
      <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--rule)', background: 'var(--surface)' }}>
        <div style={{ width: 32, height: 2, background: 'var(--accent)', marginBottom: 12 }} />
        <h1 style={{ margin: '0 0 4px', fontFamily: 'var(--font-lora, Georgia, serif)', fontSize: '1.375rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.01em' }}>
          Upload Trial Balance
        </h1>
        <p style={{ margin: 0, fontSize: '0.82rem', fontStyle: 'italic', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-40)' }}>
          Upload your VAS General Ledger for IFRS transformation
        </p>
      </div>

      <div style={{ padding: '32px', maxWidth: 640 }}>
        <div style={{
          border: '2px dashed var(--rule-strong)', borderRadius: 6,
          padding: '48px 32px', textAlign: 'center',
          background: 'var(--surface)', cursor: 'pointer',
        }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)'; (e.currentTarget as HTMLElement).style.background = 'var(--accent-light)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--rule-strong)'; (e.currentTarget as HTMLElement).style.background = 'var(--surface)' }}
        >
          <div style={{ width: 40, height: 40, borderRadius: 6, background: 'var(--paper-alt)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--ink-40)" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
              <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
            </svg>
          </div>
          <p style={{ margin: '0 0 6px', fontFamily: 'var(--font-lora, Georgia, serif)', fontSize: '0.9375rem', fontWeight: 600, color: 'var(--ink)' }}>
            Drop your trial balance here
          </p>
          <p style={{ margin: '0 0 16px', fontSize: '0.78rem', fontStyle: 'italic', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-40)' }}>
            or click to browse files
          </p>
          <p style={{ margin: 0, fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-20)', letterSpacing: '0.04em' }}>
            SUPPORTED: .xlsx · .csv · .xls · max 50 MB
          </p>
        </div>

        <div style={{ marginTop: 24, padding: '16px 20px', background: 'var(--paper-alt)', borderRadius: 4, borderLeft: '3px solid var(--accent)' }}>
          <p style={{ margin: '0 0 8px', fontSize: '0.7rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--ink-60)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            Required Format
          </p>
          <ul style={{ margin: 0, padding: '0 0 0 16px' }}>
            {['Column A: VAS account code (e.g., 1111, 2113)', 'Column B: Account description', 'Column C: Debit balance', 'Column D: Credit balance'].map(item => (
              <li key={item} style={{ fontSize: '0.78rem', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-60)', marginBottom: 4, lineHeight: 1.5 }}>
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
