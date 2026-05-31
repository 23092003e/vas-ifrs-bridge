"use client";

import { createClient } from "@/lib/supabase/client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

function EyeIcon({ open }: { open: boolean }) {
	return open ? (
		<svg
			width="14"
			height="14"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
			<circle cx="12" cy="12" r="3" />
		</svg>
	) : (
		<svg
			width="14"
			height="14"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
			<path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
			<line x1="1" y1="1" x2="23" y2="23" />
		</svg>
	);
}

function FieldInput({
	label,
	type,
	value,
	onChange,
	placeholder,
	autoFocus,
}: {
	label: string;
	type: string;
	value: string;
	onChange: (v: string) => void;
	placeholder?: string;
	autoFocus?: boolean;
}) {
	return (
		<div className="auth-field">
			<label className="auth-label">{label.toUpperCase()}</label>
			<div className="auth-input-wrap">
				<input
					type={type}
					value={value}
					placeholder={placeholder}
					autoFocus={autoFocus}
					onChange={(e) => onChange(e.target.value)}
					className="auth-input"
				/>
			</div>
		</div>
	);
}

export default function LoginPage() {
	const router = useRouter();
	const [mode, setMode] = useState<"signin" | "signup">("signin");
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [name, setName] = useState("");
	const [workspace, setWorkspace] = useState("");
	const [showPw, setShowPw] = useState(false);
	const [remember, setRemember] = useState(true);
	const [error, setError] = useState("");
	const [loading, setLoading] = useState(false);

	function validate(): string {
		if (!email.trim() || !/^\S+@\S+\.\S+$/.test(email))
			return "Email không hợp lệ.";
		if (password.length < 6) return "Mật khẩu cần tối thiểu 6 ký tự.";
		if (mode === "signup" && !name.trim()) return "Vui lòng nhập họ và tên.";
		return "";
	}

	async function handleSubmit(e: React.FormEvent) {
		e.preventDefault();
		setError("");
		const msg = validate();
		if (msg) {
			setError(msg);
			return;
		}
		setLoading(true);
		try {
			const supabase = createClient();
			if (mode === "signin") {
				const { error: err } = await supabase.auth.signInWithPassword({
					email,
					password,
				});
				if (err) {
					setError(err.message);
					return;
				}
			} else {
				const tenantId = crypto.randomUUID();
				const { error: err } = await supabase.auth.signUp({
					email,
					password,
					options: {
						data: {
							full_name: name,
							workspace: workspace || "Default Workspace",
							tenant_id: tenantId,
							role: "admin",
						},
					},
				});
				if (err) {
					setError(err.message);
					return;
				}
			}
			router.push("/chat");
			router.refresh();
		} catch {
			setError("Đã xảy ra lỗi. Vui lòng thử lại.");
		} finally {
			setLoading(false);
		}
	}

	async function handleGoogleSSO() {
		const supabase = createClient();
		await supabase.auth.signInWithOAuth({
			provider: "google",
			options: { redirectTo: `${window.location.origin}/auth/callback` },
		});
	}

	async function handleMicrosoftSSO() {
		const supabase = createClient();
		await supabase.auth.signInWithOAuth({
			provider: "azure",
			options: { redirectTo: `${window.location.origin}/auth/callback` },
		});
	}

	return (
		<main className="auth">
			{/* Left brand panel */}
			<div className="auth-brand">
				<div
					style={{
						display: "flex",
						alignItems: "center",
						gap: 12,
						marginBottom: "auto",
					}}
				>
					<div
						style={{
							width: 32,
							height: 32,
							background: "var(--accent)",
							borderRadius: 4,
							display: "flex",
							alignItems: "center",
							justifyContent: "center",
						}}
					>
						<svg
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="white"
							strokeWidth="1.75"
							strokeLinecap="round"
							strokeLinejoin="round"
						>
							<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
							<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
						</svg>
					</div>
					<div>
						<p
							style={{
								margin: 0,
								fontSize: "0.875rem",
								fontWeight: 700,
								color: "#f5f5f4",
								fontFamily: "var(--font-lora, Georgia, serif)",
								letterSpacing: "-0.01em",
							}}
						>
							VAS·IFRS
						</p>
						<p
							style={{
								margin: 0,
								fontSize: "0.58rem",
								color: "#a8a29e",
								letterSpacing: "0.08em",
								textTransform: "uppercase",
								fontWeight: 500,
								fontFamily: "var(--font-mono)",
							}}
						>
							Knowledge Engine
						</p>
					</div>
				</div>

				<div style={{ margin: "auto 0" }}>
					<h1 className="auth-headline">
						Tra cứu chuẩn mực kế toán — <em>dẫn về điều khoản gốc.</em>
					</h1>
					<p className="auth-sub">
						Trợ lý AI hiểu VAS và IFRS, trả lời có trích dẫn nguồn, đối chiếu
						chéo giữa hai khung chuẩn mực.
					</p>
					<div className="auth-quote">
						<p className="auth-quote-text">
							"An entity shall recognise revenue when it satisfies a performance
							obligation by transferring a promised good or service to a
							customer."
						</p>
						<p className="auth-quote-meta">IFRS 15 · §31 · IASB</p>
					</div>
				</div>

				<div className="auth-brand-foot">
					{["SOC 2 · Type II", "Data residency · VN", "v2.4.1"].map((p) => (
						<span key={p}>{p}</span>
					))}
				</div>
			</div>

			{/* Right form panel */}
			<div className="auth-form-side">
				<div className="auth-form-side-top">
					<span>
						{mode === "signin" ? "Chưa có tài khoản?" : "Đã có tài khoản?"}
					</span>
					<button
						type="button"
						onClick={() => {
							setMode((m) => (m === "signin" ? "signup" : "signin"));
							setError("");
						}}
						style={{
							background: "none",
							border: "none",
							cursor: "pointer",
							color: "var(--accent)",
							fontSize: "0.7rem",
							fontWeight: 700,
							fontFamily: "var(--font-mono)",
							padding: 0,
						}}
					>
						{mode === "signin" ? "Đăng ký" : "Đăng nhập"}
					</button>
				</div>

				<div className="auth-form">
					<div style={{ marginBottom: 28 }}>
						<h2 className="auth-title">
							{mode === "signin"
								? "Đăng nhập vào workspace"
								: "Tạo tài khoản mới"}
						</h2>
						<p className="auth-desc">
							{mode === "signin"
								? "Sử dụng email công ty để truy cập cơ sở tri thức."
								: "Một tài khoản cho cả nhóm — admin mời thành viên sau."}
						</p>
					</div>

					{/* SSO */}
					<div className="auth-sso">
						<button
							type="button"
							className="auth-sso-btn"
							onClick={handleGoogleSSO}
						>
							<svg
								viewBox="0 0 24 24"
								width="17"
								height="17"
								style={{ flexShrink: 0 }}
							>
								<path
									fill="#4285F4"
									d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
								/>
								<path
									fill="#34A853"
									d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
								/>
								<path
									fill="#FBBC05"
									d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
								/>
								<path
									fill="#EA4335"
									d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
								/>
							</svg>
							<span style={{ flex: 1 }}>Tiếp tục với Google</span>
							<small>SSO</small>
						</button>
						<button
							type="button"
							className="auth-sso-btn"
							onClick={handleMicrosoftSSO}
						>
							<svg
								viewBox="0 0 24 24"
								width="16"
								height="16"
								style={{ flexShrink: 0 }}
							>
								<path fill="#F25022" d="M2 2h9.5v9.5H2z" />
								<path fill="#7FBA00" d="M12.5 2H22v9.5h-9.5z" />
								<path fill="#00A4EF" d="M2 12.5h9.5V22H2z" />
								<path fill="#FFB900" d="M12.5 12.5H22V22h-9.5z" />
							</svg>
							<span style={{ flex: 1 }}>Tiếp tục với Microsoft</span>
							<small>SSO</small>
						</button>
					</div>

					<div className="auth-divider">
						<span>hoặc dùng email</span>
					</div>

					<form onSubmit={handleSubmit} noValidate className="auth-fields">
						{mode === "signup" && (
							<>
								<FieldInput
									label="Họ và tên"
									type="text"
									value={name}
									onChange={setName}
									placeholder="Nguyễn Văn A"
								/>
								<FieldInput
									label="Workspace"
									type="text"
									value={workspace}
									onChange={setWorkspace}
									placeholder="firm-name (tuỳ chọn)"
								/>
							</>
						)}

						<FieldInput
							label="Email công ty"
							type="email"
							value={email}
							onChange={setEmail}
							placeholder="ban@firm.vn"
							autoFocus
						/>

						{/* Password field */}
						<div className="auth-field">
							<label className="auth-label">
								<span>MẬT KHẨU</span>
								{mode === "signin" && (
									<a href="#" onClick={(e) => e.preventDefault()}>
										Quên mật khẩu?
									</a>
								)}
							</label>
							<div className="auth-input-wrap">
								<input
									type={showPw ? "text" : "password"}
									value={password}
									onChange={(e) => setPassword(e.target.value)}
									placeholder="••••••••"
									className="auth-input"
									autoComplete={
										mode === "signin" ? "current-password" : "new-password"
									}
								/>
								<button
									type="button"
									onClick={() => setShowPw((s) => !s)}
									className="auth-input-toggle"
									title={showPw ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
								>
									<EyeIcon open={showPw} />
								</button>
							</div>
						</div>

						{mode === "signin" && (
							<label
								style={{
									display: "flex",
									alignItems: "center",
									gap: 8,
									cursor: "pointer",
									userSelect: "none",
								}}
							>
								<input
									type="checkbox"
									checked={remember}
									onChange={(e) => setRemember(e.target.checked)}
									style={{
										accentColor: "var(--accent)",
										width: 14,
										height: 14,
										cursor: "pointer",
									}}
								/>
								<span
									style={{
										fontSize: "0.75rem",
										color: "var(--ink-60)",
										fontFamily: "var(--font-lora, Georgia, serif)",
									}}
								>
									Ghi nhớ thiết bị này
								</span>
								<span
									style={{
										marginLeft: "auto",
										fontSize: "0.62rem",
										color: "var(--ink-20)",
										fontFamily: "var(--font-mono)",
									}}
								>
									SSO · SAML
								</span>
							</label>
						)}

						{error && <div className="auth-err">{error}</div>}

						<button type="submit" disabled={loading} className="auth-submit">
							{loading
								? mode === "signin"
									? "ĐANG ĐĂNG NHẬP…"
									: "ĐANG TẠO TÀI KHOẢN…"
								: mode === "signin"
									? "ĐĂNG NHẬP"
									: "TẠO TÀI KHOẢN"}
						</button>
					</form>

					<p className="auth-foot-note">
						<Link
							href="/chat"
							style={{ color: "var(--ink-20)", textDecoration: "none" }}
						>
							© 2026 VAS·IFRS
						</Link>
						{" · "}
						<a href="#">Trạng thái</a>
						{" · "}
						<a href="#">Tài liệu</a>
						{" · "}
						<a href="#">Hỗ trợ</a>
					</p>
				</div>
			</div>
		</main>
	);
}
