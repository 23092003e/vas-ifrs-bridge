'use client'

export default function SettingsAuditPage() {
  const logs = [
    { ts: '2025-05-20 14:32:11', user: 'vana@company.com', action: 'GL_UPLOAD', resource: 'trial_balance_q1_2025.xlsx', ip: '192.168.1.42', result: 'Success' },
    { ts: '2025-05-20 11:18:04', user: 'thib@company.com', action: 'ADJ_APPROVE', resource: 'ADJ-003 (IFRS 9 ECL)', ip: '10.0.0.15', result: 'Success' },
    { ts: '2025-05-19 16:45:22', user: 'vanc@company.com', action: 'REPORT_EXPORT', resource: 'IFRS_Transition_FY2024.pdf', ip: '192.168.1.88', result: 'Success' },
    { ts: '2025-05-19 09:22:38', user: 'thib@company.com', action: 'USER_INVITE', resource: 'vane@company.com (Viewer)', ip: '10.0.0.15', result: 'Success' },
    { ts: '2025-05-18 17:03:55', user: 'vana@company.com', action: 'SETTINGS_UPDATE', resource: 'Tenant billing email', ip: '192.168.1.42', result: 'Success' },
    { ts: '2025-05-18 10:11:29', user: 'thid@company.com', action: 'KB_QUERY', resource: 'IFRS 9 — impairment model', ip: '10.0.1.7', result: 'Success' },
    { ts: '2025-05-17 14:55:01', user: 'vanc@company.com', action: 'LOGIN', resource: '—', ip: '192.168.1.88', result: 'Success' },
    { ts: '2025-05-17 08:34:17', user: 'unknown', action: 'LOGIN', resource: '—', ip: '203.0.113.55', result: 'Failed' },
  ]

  const actionColor = (a: string) => {
    if (a === 'LOGIN') return 'var(--ink-40)'
    if (a.includes('APPROVE')) return 'var(--score-high)'
    if (a.includes('EXPORT') || a.includes('REPORT')) return 'var(--score-mid)'
    return 'var(--accent)'
  }
  const resultColor = (r: string) => r === 'Success' ? 'var(--score-high)' : 'var(--accent)'

  return (
    <div style={{ flex: 1, overflow: 'auto', background: 'var(--chat-bg)' }}>
      <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--rule)', background: 'var(--surface)', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
        <div>
          <div style={{ width: 32, height: 2, background: 'var(--accent)', marginBottom: 12 }} />
          <h1 style={{ margin: '0 0 4px', fontFamily: 'var(--font-lora, Georgia, serif)', fontSize: '1.375rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.01em' }}>Audit Trail</h1>
          <p style={{ margin: 0, fontSize: '0.82rem', fontStyle: 'italic', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-40)' }}>Immutable log of all system actions and access events</p>
        </div>
        <button type="button" style={{ padding: '8px 16px', borderRadius: 3, background: 'transparent', color: 'var(--ink-60)', border: '1px solid var(--rule-strong)', fontSize: '0.72rem', fontWeight: 700, fontFamily: 'var(--font-mono)', letterSpacing: '0.05em', cursor: 'pointer' }}>EXPORT LOG</button>
      </div>

      <div style={{ padding: '12px 32px', borderBottom: '1px solid var(--rule)', background: 'var(--paper-alt)', display: 'flex', gap: 40 }}>
        {[['Events (30d)', '847'], ['Failed Attempts', '3'], ['Unique Users', '5'], ['Retention', '90 days']].map(([l, v]) => (
          <div key={l}>
            <p style={{ margin: '0 0 2px', fontSize: '0.6rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-40)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{l}</p>
            <p style={{ margin: 0, fontSize: '1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--ink)' }}>{v}</p>
          </div>
        ))}
      </div>

      <div style={{ padding: '24px 32px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid var(--ink)' }}>
              {['Timestamp', 'User', 'Action', 'Resource', 'IP Address', 'Result'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '0.6rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--ink-60)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.map((l, i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--rule)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--accent-light)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}
              >
                <td style={{ padding: '9px 12px' }}><span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-60)' }}>{l.ts}</span></td>
                <td style={{ padding: '9px 12px' }}><span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--ink)' }}>{l.user}</span></td>
                <td style={{ padding: '9px 12px' }}><span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: actionColor(l.action) }}>{l.action}</span></td>
                <td style={{ padding: '9px 12px', fontSize: '0.73rem', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-60)', maxWidth: 240 }}>{l.resource}</td>
                <td style={{ padding: '9px 12px' }}><span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-40)' }}>{l.ip}</span></td>
                <td style={{ padding: '9px 12px' }}><span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: resultColor(l.result) }}>{l.result}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ marginTop: 16, fontSize: '0.68rem', fontStyle: 'italic', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-20)' }}>
          Showing 8 of 847 events. Audit logs are retained for 90 days and cannot be modified.
        </p>
      </div>
    </div>
  )
}
