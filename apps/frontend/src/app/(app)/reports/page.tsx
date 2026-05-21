'use client'

export default function ReportsPage() {
  const reports = [
    { name: 'IFRS Transition Report — FY2024', type: 'Transition', status: 'Ready', date: '2025-05-15', size: '2.1 MB' },
    { name: 'VAS to IFRS Adjustment Summary', type: 'Adjustment', status: 'Ready', date: '2025-05-10', size: '0.8 MB' },
    { name: 'Statement of Financial Position', type: 'Financial', status: 'Ready', date: '2025-04-30', size: '0.5 MB' },
    { name: 'Comprehensive Income Statement', type: 'Financial', status: 'Generating', date: '—', size: '—' },
    { name: 'Disclosure Notes — IFRS 7', type: 'Disclosure', status: 'Draft', date: '2025-05-20', size: '1.2 MB' },
  ]

  const statusColor = (s: string) => s === 'Ready' ? 'var(--score-high)' : s === 'Generating' ? 'var(--score-mid)' : 'var(--ink-40)'

  return (
    <div style={{ flex: 1, overflow: 'auto', background: 'var(--chat-bg)' }}>
      <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--rule)', background: 'var(--surface)', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
        <div>
          <div style={{ width: 32, height: 2, background: 'var(--accent)', marginBottom: 12 }} />
          <h1 style={{ margin: '0 0 4px', fontFamily: 'var(--font-lora, Georgia, serif)', fontSize: '1.375rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.01em' }}>
            Financial Reports
          </h1>
          <p style={{ margin: 0, fontSize: '0.82rem', fontStyle: 'italic', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-40)' }}>
            Generated IFRS-compliant financial statements and transition reports
          </p>
        </div>
        <button type="button" style={{ padding: '8px 16px', borderRadius: 3, background: 'var(--accent)', color: '#fff', border: 'none', fontSize: '0.72rem', fontWeight: 700, fontFamily: 'var(--font-mono)', letterSpacing: '0.05em', cursor: 'pointer' }}>
          + GENERATE REPORT
        </button>
      </div>

      <div style={{ padding: '24px 32px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid var(--ink)' }}>
              {['Report Name', 'Type', 'Status', 'Generated', 'Size'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '0.6rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--ink-60)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {reports.map((r, i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--rule)', cursor: 'pointer' }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--accent-light)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}
              >
                <td style={{ padding: '12px 12px' }}>
                  <span style={{ fontSize: '0.82rem', fontFamily: 'var(--font-lora, Georgia, serif)', fontWeight: 600, color: 'var(--ink)' }}>{r.name}</span>
                </td>
                <td style={{ padding: '12px 12px' }}>
                  <span style={{ fontSize: '0.63rem', fontFamily: 'var(--font-mono)', padding: '2px 6px', borderRadius: 2, background: 'var(--paper-alt)', color: 'var(--ink-60)' }}>{r.type}</span>
                </td>
                <td style={{ padding: '12px 12px' }}>
                  <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: statusColor(r.status) }}>{r.status}</span>
                </td>
                <td style={{ padding: '12px 12px', fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-40)' }}>{r.date}</td>
                <td style={{ padding: '12px 12px', fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-40)' }}>{r.size}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
