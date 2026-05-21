'use client'

import { useState } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'

function EyeIcon({ open }: { open: boolean }) {
  return open ? (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )
}

function FieldInput({ label, type, value, onChange, placeholder, autoFocus }: {
  label: string; type: string; value: string
  onChange: (v: string) => void; placeholder?: string; autoFocus?: boolean
}) {
  const [focused, setFocused] = useState(false)
  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.68rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--ink-60)', letterSpacing: '0.07em', marginBottom: 6 }}>
        {label.toUpperCase()}
      </label>
      <input
        type={type} value={value} placeholder={placeholder} autoFocus={autoFocus}
        onChange={e => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          width: '100%', padding: '10px 12px', fontSize: '0.875rem',
          fontFamily: 'var(--font-lora, Georgia, serif)',
          border: `1.5px solid ${focused ? 'var(--accent)' : 'var(--rule-strong)'}`,
          borderRadius: 3, background: 'var(--surface)', color: 'var(--ink)', outline: 'none',
          boxShadow: focused ? 'var(--input-focus-shadow)' : 'none',
          transition: 'border-color 150ms, box-shadow 150ms', boxSizing: 'border-box',
        }}
      />
    </div>
  )
}

export default function LoginPage() {
  const router = useRouter()
  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [workspace, setWorkspace] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [remember, setRemember] = useState(true)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [pwFocused, setPwFocused] = useState(false)

  function validate(): string {
    if (!email.trim() || !/^\S+@\S+\.\S+$/.test(email)) return 'Email không hợp lệ.'
    if (password.length < 6) return 'Mật khẩu cần tối thiểu 6 ký tự.'
    if (mode === 'signup' && !name.trim()) return 'Vui lòng nhập họ và tên.'
    return ''
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    const msg = validate()
    if (msg) { setError(msg); return }
    setLoading(true)
    try {
      const supabase = createClient()
      if (mode === 'signin') {
        const { error: err } = await supabase.auth.signInWithPassword({ email, password })
        if (err) { setError(err.message); return }
      } else {
        const { error: err } = await supabase.auth.signUp({
          email, password,
          options: { data: { full_name: name, workspace: workspace || 'Default' } },
        })
        if (err) { setError(err.message); return }
      }
      router.push('/chat')
      router.refresh()
    } catch {
      setError('Đã xảy ra lỗi. Vui lòng thử lại.')
    } finally {
      setLoading(false)
    }
  }

  async function handleGoogleSSO() {
    const supabase = createClient()
    await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: `${window.location.origin}/auth/callback` } })
  }

  async function handleMicrosoftSSO() {
    const supabase = createClient()
    await supabase.auth.signInWithOAuth({ provider: 'azure', options: { redirectTo: `${window.location.origin}/auth/callback` } })
  }

  return (
    <main className="auth-page">
      {/* Left brand panel */}
      <div className="auth-brand-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 32, height: 32, background: 'var(--accent)', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
          </div>
          <div>
            <p style={{ margin: 0, fontSize: '0.875rem', fontWeight: 700, color: '#f5f5f4', fontFamily: 'var(--font-lora, Georgia, serif)', letterSpacing: '-0.01em' }}>VAS·IFRS</p>
            <p style={{ margin: 0, fontSize: '0.58rem', color: '#a8a29e', letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 500, fontFamily: 'var(--font-mono)' }}>Knowledge Engine</p>
          </div>
        </div>

        <div>
          <div style={{ width: 40, height: 2, background: 'var(--accent)', marginBottom: 24 }} />
          <h1 style={{ margin: '0 0 16px', fontFamily: 'var(--font-lora, Georgia, serif)', fontSize: '1.875rem', fontWeight: 700, color: '#f5f5f4', lineHeight: 1.25, letterSpacing: '-0.02em' }}>
            Tra cứu chuẩn mực kế toán —{' '}
            <em style={{ fontStyle: 'italic', color: '#d6d3d1' }}>dẫn về điều khoản gốc.</em>
          </h1>
          <p style={{ margin: '0 0 28px', fontFamily: 'var(--font-lora, Georgia, serif)', fontSize: '0.9375rem', fontStyle: 'italic', color: '#a8a29e', lineHeight: 1.7 }}>
            Trợ lý AI hiểu VAS và IFRS, trả lời có trích dẫn nguồn, đối chiếu chéo giữa hai khung chuẩn mực.
          </p>
          <div style={{ borderLeft: '3px solid var(--accent)', paddingLeft: 16 }}>
            <p style={{ margin: '0 0 8px', fontFamily: 'var(--font-lora, Georgia, serif)', fontStyle: 'italic', fontSize: '0.875rem', color: '#d6d3d1', lineHeight: 1.7 }}>
              "An entity shall recognise revenue when it satisfies a performance obligation by transferring a promised good or service to a customer."
            </p>
            <p style={{ margin: 0, fontSize: '0.6rem', fontFamily: 'var(--font-mono)', color: '#78716c', letterSpacing: '0.06em' }}>IFRS 15 · §31 · IASB</p>
          </div>
        </div>

        <div className="auth-foot-pills">
          {['SOC 2 · Type II', 'Data residency · VN', 'v2.4.1'].map(p => (
            <span key={p} className="auth-foot-pill">{p}</span>
          ))}
        </div>
      </div>

      {/* Right form panel */}
      <div className="auth-form-panel">
        <div className="auth-form-panel-top">
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
            {mode === 'signin' ? 'Chưa có tài khoản?' : 'Đã có tài khoản?'}
          </span>
          <button
            type="button"
            onClick={() => { setMode(m => m === 'signin' ? 'signup' : 'signin'); setError('') }}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', fontSize: '0.7rem', fontWeight: 700, fontFamily: 'var(--font-mono)', padding: 0 }}
          >
            {mode === 'signin' ? 'Đăng ký' : 'Đăng nhập'}
          </button>
        </div>

        <div style={{ width: '100%', maxWidth: 400 }}>
          <div style={{ marginBottom: 28 }}>
            <div style={{ width: 32, height: 2, background: 'var(--accent)', marginBottom: 16 }} />
            <h2 style={{ margin: '0 0 6px', fontFamily: 'var(--font-lora, Georgia, serif)', fontSize: '1.5rem', fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.01em' }}>
              {mode === 'signin' ? 'Đăng nhập vào workspace' : 'Tạo tài khoản mới'}
            </h2>
            <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--ink-40)', fontStyle: 'italic', fontFamily: 'var(--font-lora, Georgia, serif)' }}>
              {mode === 'signin'
                ? 'Sử dụng email công ty để truy cập cơ sở tri thức.'
                : 'Một tài khoản cho cả nhóm — admin mời thành viên sau.'}
            </p>
          </div>

          {/* SSO */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <button type="button" className="auth-sso-btn" onClick={handleGoogleSSO}>
              <svg viewBox="0 0 24 24" width="17" height="17" style={{ flexShrink: 0 }}>
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              <span style={{ flex: 1 }}>Tiếp tục với Google</span>
              <span className="auth-sso-tag">SSO</span>
            </button>
            <button type="button" className="auth-sso-btn" onClick={handleMicrosoftSSO}>
              <svg viewBox="0 0 24 24" width="16" height="16" style={{ flexShrink: 0 }}>
                <path fill="#F25022" d="M2 2h9.5v9.5H2z" />
                <path fill="#7FBA00" d="M12.5 2H22v9.5h-9.5z" />
                <path fill="#00A4EF" d="M2 12.5h9.5V22H2z" />
                <path fill="#FFB900" d="M12.5 12.5H22V22h-9.5z" />
              </svg>
              <span style={{ flex: 1 }}>Tiếp tục với Microsoft</span>
              <span className="auth-sso-tag">SSO</span>
            </button>
          </div>

          <div className="auth-divider"><span>hoặc dùng email</span></div>

          <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {mode === 'signup' && (
              <>
                <FieldInput label="Họ và tên" type="text" value={name} onChange={setName} placeholder="Nguyễn Văn A" />
                <FieldInput label="Workspace" type="text" value={workspace} onChange={setWorkspace} placeholder="firm-name (tuỳ chọn)" />
              </>
            )}

            <FieldInput label="Email công ty" type="email" value={email} onChange={setEmail} placeholder="ban@firm.vn" autoFocus />

            {/* Password field */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
                <label style={{ fontSize: '0.68rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--ink-60)', letterSpacing: '0.07em' }}>
                  MẬT KHẨU
                </label>
                {mode === 'signin' && (
                  <a href="#" style={{ fontSize: '0.7rem', color: 'var(--accent)', textDecoration: 'none' }}>Quên mật khẩu?</a>
                )}
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                  onFocus={() => setPwFocused(true)}
                  onBlur={() => setPwFocused(false)}
                  style={{
                    width: '100%', padding: '10px 40px 10px 12px', fontSize: '0.875rem',
                    fontFamily: 'var(--font-lora, Georgia, serif)',
                    border: `1.5px solid ${pwFocused ? 'var(--accent)' : 'var(--rule-strong)'}`,
                    borderRadius: 3, background: 'var(--surface)', color: 'var(--ink)', outline: 'none',
                    boxShadow: pwFocused ? 'var(--input-focus-shadow)' : 'none',
                    transition: 'border-color 150ms, box-shadow 150ms', boxSizing: 'border-box',
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(s => !s)}
                  style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink-40)', display: 'flex', alignItems: 'center', padding: 2 }}
                  title={showPw ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  <EyeIcon open={showPw} />
                </button>
              </div>
            </div>

            {mode === 'signin' && (
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', userSelect: 'none' }}>
                <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} style={{ accentColor: 'var(--accent)', width: 14, height: 14, cursor: 'pointer' }} />
                <span style={{ fontSize: '0.75rem', color: 'var(--ink-60)', fontFamily: 'var(--font-lora, Georgia, serif)' }}>Ghi nhớ thiết bị này</span>
                <span style={{ marginLeft: 'auto', fontSize: '0.62rem', color: 'var(--ink-20)', fontFamily: 'var(--font-mono)' }}>SSO · SAML</span>
              </label>
            )}

            {error && <div className="auth-err">{error}</div>}

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%', padding: '11px', borderRadius: 3, marginTop: 2,
                background: loading ? 'var(--rule-strong)' : 'var(--accent)',
                color: '#fff', border: 'none', cursor: loading ? 'wait' : 'pointer',
                fontSize: '0.78rem', fontWeight: 700, fontFamily: 'var(--font-mono)',
                letterSpacing: '0.06em', transition: 'background 150ms',
              }}
              onMouseEnter={e => { if (!loading) (e.currentTarget as HTMLElement).style.background = 'var(--accent-hover)' }}
              onMouseLeave={e => { if (!loading) (e.currentTarget as HTMLElement).style.background = 'var(--accent)' }}
            >
              {loading
                ? (mode === 'signin' ? 'ĐANG ĐĂNG NHẬP…' : 'ĐANG TẠO TÀI KHOẢN…')
                : (mode === 'signin' ? 'ĐĂNG NHẬP' : 'TẠO TÀI KHOẢN')}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: 20, fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-40)' }}>
            <Link href="/chat" style={{ color: 'var(--ink-20)', textDecoration: 'none' }}>© 2026 VAS·IFRS</Link>
            {' · '}
            <a href="#" style={{ color: 'var(--ink-40)', textDecoration: 'none' }}>Trạng thái</a>
            {' · '}
            <a href="#" style={{ color: 'var(--ink-40)', textDecoration: 'none' }}>Tài liệu</a>
            {' · '}
            <a href="#" style={{ color: 'var(--ink-40)', textDecoration: 'none' }}>Hỗ trợ</a>
          </p>
        </div>
      </div>
    </main>
  )
}
