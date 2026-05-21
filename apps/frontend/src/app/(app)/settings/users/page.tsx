'use client'

export default function SettingsUsersPage() {
  const users = [
    { name: 'Nguyễn Văn A', email: 'vana@company.com', role: 'Owner', lastActive: '2025-05-20', status: 'Active' },
    { name: 'Trần Thị B', email: 'thib@company.com', role: 'Admin', lastActive: '2025-05-19', status: 'Active' },
    { name: 'Lê Văn C', email: 'vanc@company.com', role: 'Accountant', lastActive: '2025-05-18', status: 'Active' },
    { name: 'Phạm Thị D', email: 'thid@company.com', role: 'Auditor', lastActive: '2025-05-15', status: 'Active' },
    { name: 'Hoàng Văn E', email: 'vane@company.com', role: 'Viewer', lastActive: '—', status: 'Pending' },
  ]

  const roleColor = (r: string) => {
    if (r === 'Owner') return 'var(--accent)'
    if (r === 'Admin') return 'var(--score-mid)'
    if (r === 'Accountant') return 'var(--score-high)'
    return 'var(--ink-40)'
  }
  const statusColor = (s: string) => s === 'Active' ? 'var(--score-high)' : 'var(--score-mid)'

  return (
    <div style={{ flex: 1, overflow: 'auto', background: 'var(--chat-bg)' }}>
      <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--rule)', background: 'var(--surface)', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
        <div>
          <div style={{ width: 32, height: 2, background: 'var(--accent)', marginBottom: 12 }} />
          <h1 style={{ margin: '0 0 4px', fontFamily: 'var(--font-lora, Georgia, serif)', fontSize: '1.375rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.01em' }}>Team Members</h1>
          <p style={{ margin: 0, fontSize: '0.82rem', fontStyle: 'italic', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-40)' }}>Manage access and roles for your organisation</p>
        </div>
        <button type="button" style={{ padding: '8px 16px', borderRadius: 3, background: 'var(--accent)', color: '#fff', border: 'none', fontSize: '0.72rem', fontWeight: 700, fontFamily: 'var(--font-mono)', letterSpacing: '0.05em', cursor: 'pointer' }}>+ INVITE USER</button>
      </div>

      <div style={{ padding: '12px 32px', borderBottom: '1px solid var(--rule)', background: 'var(--paper-alt)', display: 'flex', gap: 40 }}>
        {[['Total Members', '5'], ['Active', '4'], ['Pending Invitation', '1'], ['Roles Available', '5']].map(([l, v]) => (
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
              {['Name', 'Email', 'Role', 'Last Active', 'Status', ''].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '0.6rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--ink-60)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map((u, i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--rule)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--accent-light)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}
              >
                <td style={{ padding: '10px 12px', fontSize: '0.82rem', fontFamily: 'var(--font-lora, Georgia, serif)', fontWeight: 600, color: 'var(--ink)' }}>{u.name}</td>
                <td style={{ padding: '10px 12px' }}><span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-60)' }}>{u.email}</span></td>
                <td style={{ padding: '10px 12px' }}><span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: roleColor(u.role) }}>{u.role.toUpperCase()}</span></td>
                <td style={{ padding: '10px 12px', fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-40)' }}>{u.lastActive}</td>
                <td style={{ padding: '10px 12px' }}><span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: statusColor(u.status) }}>{u.status}</span></td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  <button type="button" style={{ fontSize: '0.63rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-40)', background: 'transparent', border: '1px solid var(--rule-strong)', borderRadius: 2, padding: '3px 8px', cursor: 'pointer' }}>MANAGE</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ margin: '0 32px', padding: '16px 20px', background: 'var(--paper-alt)', borderRadius: 4, borderLeft: '3px solid var(--rule-strong)', maxWidth: 560 }}>
        <p style={{ margin: '0 0 4px', fontSize: '0.65rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--ink-60)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Role Hierarchy</p>
        <p style={{ margin: 0, fontSize: '0.78rem', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-60)', lineHeight: 1.6 }}>
          Viewer → Auditor → Accountant → Admin → Owner. Each role inherits all permissions of lower roles.
        </p>
      </div>
    </div>
  )
}
