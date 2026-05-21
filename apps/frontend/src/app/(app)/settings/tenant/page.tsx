'use client'

export default function SettingsTenantPage() {
  function field(label: string, value: string, mono = false) {
    return (
      <div style={{ marginBottom: 20 }}>
        <label style={{ display: 'block', fontSize: '0.65rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--ink-60)', letterSpacing: '0.07em', marginBottom: 6 }}>{label}</label>
        <input type="text" defaultValue={value} style={{
          width: '100%', padding: '9px 12px',
          fontSize: mono ? '0.82rem' : '0.875rem',
          fontFamily: mono ? 'var(--font-mono)' : 'var(--font-lora, Georgia, serif)',
          border: '1.5px solid var(--rule-strong)', borderRadius: 3,
          background: 'var(--surface)', color: 'var(--ink)', outline: 'none',
        }}
          onFocus={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.boxShadow = 'var(--input-focus-shadow)' }}
          onBlur={e => { e.currentTarget.style.borderColor = 'var(--rule-strong)'; e.currentTarget.style.boxShadow = 'none' }}
        />
      </div>
    )
  }

  return (
    <div style={{ flex: 1, overflow: 'auto', background: 'var(--chat-bg)' }}>
      <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--rule)', background: 'var(--surface)' }}>
        <div style={{ width: 32, height: 2, background: 'var(--accent)', marginBottom: 12 }} />
        <h1 style={{ margin: '0 0 4px', fontFamily: 'var(--font-lora, Georgia, serif)', fontSize: '1.375rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.01em' }}>Organisation Settings</h1>
        <p style={{ margin: 0, fontSize: '0.82rem', fontStyle: 'italic', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-40)' }}>Tenant configuration and billing</p>
      </div>
      <div style={{ padding: '32px', maxWidth: 560 }}>
        {field('ORGANISATION NAME', 'Default Organisation')}
        {field('TENANT ID', 'tenant_a1b2c3d4', true)}
        {field('BILLING EMAIL', 'admin@demo.com')}
        {field('PLAN', 'Professional — 50k queries/month')}
        <div style={{ paddingTop: 8, display: 'flex', gap: 8 }}>
          <button type="button" style={{ padding: '9px 20px', borderRadius: 3, background: 'var(--accent)', color: '#fff', border: 'none', fontSize: '0.72rem', fontWeight: 700, fontFamily: 'var(--font-mono)', letterSpacing: '0.05em', cursor: 'pointer' }}>SAVE CHANGES</button>
          <button type="button" style={{ padding: '9px 20px', borderRadius: 3, background: 'transparent', color: 'var(--ink-60)', border: '1px solid var(--rule-strong)', fontSize: '0.72rem', fontWeight: 600, fontFamily: 'var(--font-mono)', cursor: 'pointer' }}>CANCEL</button>
        </div>
      </div>
    </div>
  )
}
