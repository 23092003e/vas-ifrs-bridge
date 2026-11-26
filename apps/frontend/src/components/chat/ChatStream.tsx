"use client";

import { useChat } from "@/lib/hooks/useChat";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { type KeyboardEvent, useEffect, useRef, useState } from "react";
import { MessageList } from "./MessageList";
import { RetrievalPanel } from "./RetrievalPanel";

/* ── Icons ── */
function SendIcon() {
	return (
		<svg
			width="13"
			height="13"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2.5"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<line x1="22" y1="2" x2="11" y2="13" />
			<polygon
				points="22 2 15 22 11 13 2 9 22 2"
				fill="currentColor"
				stroke="none"
			/>
		</svg>
	);
}

function StopIcon() {
	return (
		<svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
			<rect x="4" y="4" width="16" height="16" rx="2" />
		</svg>
	);
}

function SidebarIcon() {
	return (
		<svg
			width="15"
			height="15"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<rect x="3" y="3" width="18" height="18" rx="2" />
			<line x1="9" y1="3" x2="9" y2="21" />
		</svg>
	);
}

function InspectIcon() {
	return (
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
			<circle cx="11" cy="11" r="8" />
			<line x1="21" y1="21" x2="16.65" y2="16.65" />
		</svg>
	);
}

function PlusSmIcon() {
	return (
		<svg
			width="11"
			height="11"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2.5"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<line x1="12" y1="5" x2="12" y2="19" />
			<line x1="5" y1="12" x2="19" y2="12" />
		</svg>
	);
}

function ChevronDownIcon() {
	return (
		<svg
			width="9"
			height="9"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2.5"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<polyline points="6 9 12 15 18 9" />
		</svg>
	);
}

function AttachIcon() {
	return (
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
			<path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
		</svg>
	);
}

/* ── PillDropdown ── */
interface PillDropdownProps {
	label: string;
	value: string;
	options: string[];
	onChange: (v: string) => void;
}

function PillDropdown({ label, value, options, onChange }: PillDropdownProps) {
	const [open, setOpen] = useState(false);
	const ref = useRef<HTMLDivElement>(null);

	useEffect(() => {
		if (!open) return;
		function handleClick(e: MouseEvent) {
			if (ref.current && !ref.current.contains(e.target as Node))
				setOpen(false);
		}
		document.addEventListener("mousedown", handleClick);
		return () => document.removeEventListener("mousedown", handleClick);
	}, [open]);

	return (
		<div ref={ref} style={{ position: "relative" }}>
			<button
				type="button"
				className="composer-pill"
				data-on={open ? "true" : undefined}
				onClick={() => setOpen((o) => !o)}
			>
				<span
					style={{ color: "var(--muted)", fontSize: "0.65rem", marginRight: 3 }}
				>
					{label}
				</span>
				<span>{value}</span>
				<ChevronDownIcon />
			</button>

			{open && (
				<div
					className="pill-dropdown"
					style={{
						position: "absolute",
						bottom: "calc(100% + 6px)",
						left: 0,
						zIndex: 50,
					}}
				>
					<div className="pill-dropdown-label">{label}</div>
					{options.map((opt) => (
						<button
							key={opt}
							type="button"
							className="pill-dropdown-item"
							data-selected={opt === value ? "true" : undefined}
							onClick={() => {
								onChange(opt);
								setOpen(false);
							}}
						>
							{opt}
						</button>
					))}
				</div>
			)}
		</div>
	);
}

/* ── Main component ── */
export default function ChatStream() {
	const { messages, loading, sendMessage, clearMessages, abort } = useChat();
	const searchParams = useSearchParams();
	const [input, setInput] = useState(() => searchParams?.get("q") ?? "");
	const [lang, setLang] = useState<"vi" | "en" | "auto">("auto");
	const [scope, setScope] = useState<"shared" | "tenant" | "both">("shared");
	const [reasoning, setReasoning] = useState<"fast" | "balanced" | "deep">(
		"fast",
	);
	const [drawerOpen, setDrawerOpen] = useState(true);
	const composingRef = useRef(false);
	const textareaRef = useRef<HTMLTextAreaElement>(null);

	useEffect(() => {
		const q = searchParams?.get("q");
		if (q && !input) {
			setInput(q);
		}
	}, [searchParams, input]);

	useEffect(() => {
		const handler = () => {
			clearMessages();
			setInput("");
			textareaRef.current?.focus();
		};
		window.addEventListener("vas-new-chat", handler);
		return () => window.removeEventListener("vas-new-chat", handler);
	}, [clearMessages]);

	function handleSend() {
		const q = input.trim();
		if (!q || loading) return;
		setInput("");
		if (textareaRef.current) textareaRef.current.style.height = "auto";
		sendMessage(q, {
			lang,
			scope,
			reasoning,
		});
	}

	function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
		if (e.key === "Enter" && !e.shiftKey && !composingRef.current) {
			e.preventDefault();
			handleSend();
		}
	}

	function handleInput() {
		const el = textareaRef.current;
		if (!el) return;
		el.style.height = "auto";
		el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
	}

	const canSend = input.trim().length > 0 && !loading;
	const firstUserMsg = messages.find((m) => m.role === "user")?.content;

	return (
		<div style={{ display: "flex", flex: 1, overflow: "hidden", minWidth: 0 }}>
			{/* ── Center column ── */}
			<div
				style={{
					display: "flex",
					flexDirection: "column",
					flex: 1,
					overflow: "hidden",
					background: "var(--bg)",
					minWidth: 0,
				}}
			>
				{/* Topbar */}
				<div className="topbar">
					<button
						type="button"
						className="topbar-toggle"
						title="Toggle sidebar"
						onClick={() =>
							window.dispatchEvent(new CustomEvent("vas-toggle-sidebar"))
						}
					>
						<SidebarIcon />
					</button>

					<div className="topbar-crumb">
						<span className="crumb-page">Chat</span>
						<span className="crumb-sep">/</span>
						<span className="crumb-title">
							{firstUserMsg ? firstUserMsg.slice(0, 52) : "Nova tư vấn"}
						</span>
					</div>

					<div className="topbar-actions">
						<button
							type="button"
							className="topbar-chip"
							onClick={() => {
								clearMessages();
								setInput("");
							}}
						>
							<PlusSmIcon />
							New
						</button>

						<button
							type="button"
							className="topbar-iconbtn"
							data-active={drawerOpen ? "true" : "false"}
							title="Toggle sources"
							onClick={() => setDrawerOpen((o) => !o)}
						>
							<InspectIcon />
						</button>
					</div>
				</div>

				{/* Messages */}
				<MessageList
					messages={messages}
					onSuggestion={(text) => {
						setInput(text);
						textareaRef.current?.focus();
					}}
				/>

				{/* Composer */}
				<div className="composer-wrap">
					<div className="composer">
						<textarea
							ref={textareaRef}
							value={input}
							onChange={(e) => setInput(e.target.value)}
							onKeyDown={handleKeyDown}
							onInput={handleInput}
							onCompositionStart={() => {
								composingRef.current = true;
							}}
							onCompositionEnd={() => {
								composingRef.current = false;
							}}
							placeholder="Hỏi về một chuẩn mực, một bút toán, hoặc kéo file vào để phân tích…"
							rows={1}
							disabled={loading}
						/>

						<div className="composer-bar">
							<PillDropdown
								label="Reasoning"
								value={reasoning.toUpperCase()}
								options={["FAST", "BALANCED", "DEEP"]}
								onChange={(value) =>
									setReasoning(
										value.toLowerCase() as "fast" | "balanced" | "deep",
									)
								}
							/>
							<PillDropdown
								label="Lang"
								value={lang.toUpperCase()}
								options={["EN", "VI", "AUTO"]}
								onChange={(v) =>
									setLang(v.toLowerCase() as "en" | "vi" | "auto")
								}
							/>
							<PillDropdown
								label="Scope"
								value={
									scope === "shared"
										? "SHARED"
										: scope === "both"
											? "ALL"
											: "TENANT"
								}
								options={["SHARED", "ALL", "TENANT"]}
								onChange={(v) =>
									setScope(
										v === "SHARED" ? "shared" : v === "ALL" ? "both" : "tenant",
									)
								}
							/>

							<span className="composer-spacer" />

							<Link
								href="/documents"
								className="composer-iconbtn"
								title="Upload document"
							>
								<AttachIcon />
							</Link>

							<span className="composer-hint">↵ send · ⇧↵ newline</span>

							{loading ? (
								<button
									type="button"
									className="composer-send"
									onClick={abort}
									aria-label="Dừng phản hồi"
									style={{
										background: "var(--danger)",
										color: "#fff",
										opacity: 1,
										cursor: "pointer",
									}}
								>
									<StopIcon />
								</button>
							) : (
								<button
									type="button"
									className="composer-send"
									onClick={handleSend}
									disabled={!canSend}
								>
									<SendIcon />
								</button>
							)}
						</div>
					</div>
				</div>
			</div>

			{/* ── Right drawer ── */}
			<div className="drawer-wrap" data-open={drawerOpen ? "true" : "false"}>
				<RetrievalPanel
					messages={messages}
					onClose={() => setDrawerOpen(false)}
				/>
			</div>
		</div>
	);
}
