'use client'

import Link from 'next/link'

export default function SignupPage() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'var(--font-lora, Georgia, serif)' }}>
      {/* Left brand panel */}
      <div style={{ width: '42%', background: 'var(--sidebar-bg, #1c1917)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '48px 52px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 56 }}>
            <div style={{ width: 32, height: 32, background: 'var(--accent, #9b1c1c)', borderRadius: 3, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
            </div>
            <span style={{ fontFamily: 'var(--font-mono, monospace)', fontSize: '0.75rem', fontWeight: 700, color: 'rgba(250,249,247,0.9)', letterSpacing: '0.06em' }}>VAS·IFRS</span>
          </div>

          <div style={{ width: 32, height: 2, background: 'var(--accent, #9b1c1c)', marginBottom: 20 }} />
          <h1 style={{ margin: '0 0 16px', fontSize: '2rem', fontWeight: 700, color: '#faf9f7', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
            Request Access
          </h1>
          <p style={{ margin: '0 0 40px', fontSize: '0.95rem', fontStyle: 'italic', color: 'rgba(250,249,247,0.6)', lineHeight: 1.7 }}>
            Join your organisation&apos;s workspace or request a new tenant account for VAS → IFRS transformation.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {[
              ['Hybrid RAG', 'Dense + BM25 retrieval over VAS & IFRS standards'],
              ['GL Transformation', 'Automated journal entries for IFRS adjustments'],
              ['Audit Trail', 'Full immutable log — compliant with SOC 2'],
              ['Multi-tenant', 'Isolated workspace per organisation'],
            ].map(([title, desc]) => (
              <div key={title} style={{ display: 'flex', gap: 12 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent, #9b1c1c)', marginTop: 7, flexShrink: 0 }} />
                <div>
                  <p style={{ margin: '0 0 2px', fontFamily: 'var(--font-mono, monospace)', fontSize: '0.65rem', fontWeight: 700, color: 'rgba(250,249,247,0.8)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>{title}</p>
                  <p style={{ margin: 0, fontSize: '0.78rem', color: 'rgba(250,249,247,0.45)', lineHeight: 1.5 }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p style={{ margin: 0, fontSize: '0.65rem', fontFamily: 'var(--font-mono, monospace)', color: 'rgba(250,249,247,0.25)', letterSpacing: '0.04em' }}>
          VAS·IFRS BRIDGE © 2025
        </p>
      </div>

      {/* Right form panel */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--paper, #faf9f7)', padding: '48px' }}>
        <div style={{ width: '100%', maxWidth: 400 }}>
          <h2 style={{ margin: '0 0 6px', fontSize: '1.375rem', fontWeight: 700, color: 'var(--ink, #1c1917)', letterSpacing: '-0.01em' }}>Create your account</h2>
          <p style={{ margin: '0 0 32px', fontSize: '0.82rem', fontStyle: 'italic', color: 'var(--ink-40, rgba(28,25,23,0.4))' }}>
            Already have access?{' '}
            <Link href="/login" style={{ color: 'var(--accent, #9b1c1c)', textDecoration: 'none', fontWeight: 600 }}>Sign in →</Link>
          </p>

          <form onSubmit={e => e.preventDefault()} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', gap: 12 }}>
              {[['FIRST NAME', 'text', 'Nguyễn'], ['LAST NAME', 'text', 'Văn A']].map(([label, type, placeholder]) => (
                <div key={label} style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.6rem', fontWeight: 700, fontFamily: 'var(--font-mono, monospace)', color: 'var(--ink-60, rgba(28,25,23,0.6))', letterSpacing: '0.07em', marginBottom: 6 }}>{label}</label>
                  <input
                    type={type} placeholder={placeholder}
                    style={{ width: '100%', padding: '10px 12px', fontSize: '0.875rem', fontFamily: 'var(--font-lora, Georgia, serif)', border: '1.5px solid var(--rule-strong, #c8c4bc)', borderRadius: 3, background: 'var(--surface, #fff)', color: 'var(--ink, #1c1917)', outline: 'none', boxSizing: 'border-box' }}
                    onFocus={e => { e.currentTarget.style.borderColor = 'var(--accent, #9b1c1c)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(155,28,28,0.08)' }}
                    onBlur={e => { e.currentTarget.style.borderColor = 'var(--rule-strong, #c8c4bc)'; e.currentTarget.style.boxShadow = 'none' }}
                  />
                </div>
              ))}
            </div>

            {[
              { label: 'WORK EMAIL', type: 'email', placeholder: 'you@company.com' },
              { label: 'ORGANISATION NAME', type: 'text', placeholder: 'Công ty TNHH...' },
              { label: 'PASSWORD', type: 'password', placeholder: '••••••••••••' },
              { label: 'CONFIRM PASSWORD', type: 'password', placeholder: '••••••••••••' },
            ].map(({ label, type, placeholder }) => (
              <div key={label}>
                <label style={{ display: 'block', fontSize: '0.6rem', fontWeight: 700, fontFamily: 'var(--font-mono, monospace)', color: 'var(--ink-60, rgba(28,25,23,0.6))', letterSpacing: '0.07em', marginBottom: 6 }}>{label}</label>
                <input
                  type={type} placeholder={placeholder}
                  style={{ width: '100%', padding: '10px 12px', fontSize: type === 'password' ? '1rem' : '0.875rem', fontFamily: 'var(--font-lora, Georgia, serif)', border: '1.5px solid var(--rule-strong, #c8c4bc)', borderRadius: 3, background: 'var(--surface, #fff)', color: 'var(--ink, #1c1917)', outline: 'none', boxSizing: 'border-box' }}
                  onFocus={e => { e.currentTarget.style.borderColor = 'var(--accent, #9b1c1c)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(155,28,28,0.08)' }}
                  onBlur={e => { e.currentTarget.style.borderColor = 'var(--rule-strong, #c8c4bc)'; e.currentTarget.style.boxShadow = 'none' }}
                />
              </div>
            ))}

            <button
              type="submit"
              style={{ marginTop: 8, padding: '12px', background: 'var(--accent, #9b1c1c)', color: '#fff', border: 'none', borderRadius: 3, fontSize: '0.72rem', fontWeight: 700, fontFamily: 'var(--font-mono, monospace)', letterSpacing: '0.08em', cursor: 'pointer' }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#7f1d1d' }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'var(--accent, #9b1c1c)' }}
            >
              REQUEST ACCESS
            </button>
          </form>

          <p style={{ marginTop: 24, fontSize: '0.72rem', fontStyle: 'italic', fontFamily: 'var(--font-lora, Georgia, serif)', color: 'var(--ink-40, rgba(28,25,23,0.4))', lineHeight: 1.6, textAlign: 'center' }}>
            By requesting access you agree to the Terms of Service and Privacy Policy. Accounts are reviewed within 1 business day.
          </p>
        </div>
      </div>
    </div>
  )
}
