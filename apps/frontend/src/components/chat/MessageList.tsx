"use client";

import { MOCK_RETRIEVAL_SCORES } from "@/lib/constants";
import type { Citation, Message } from "@/types/api";
import { useEffect, useRef, useState } from "react";

/* ── Icons ── */
function CopyIcon() {
	return (
		<svg
			width="13"
			height="13"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<rect x="9" y="9" width="13" height="13" rx="2" />
			<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
		</svg>
	);
}
function ThumbUpIcon() {
	return (
		<svg
			width="13"
			height="13"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z" />
			<path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
		</svg>
	);
}
function ThumbDownIcon() {
	return (
		<svg
			width="13"
			height="13"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z" />
			<path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
		</svg>
	);
}
function RegenerateIcon() {
	return (
		<svg
			width="13"
			height="13"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<polyline points="23 4 23 10 17 10" />
			<path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
		</svg>
	);
}
function ExternalLinkIcon() {
	return (
		<svg
			width="10"
			height="10"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
			<polyline points="15 3 21 3 21 9" />
			<line x1="10" y1="14" x2="21" y2="3" />
		</svg>
	);
}

/* ── Empty / welcome state ── */
const SUGGESTIONS = [
	{
		tag: "IFRS 1",
		q: "What are the key requirements and exemptions when adopting IFRS for the first time?",
	},
	{
		tag: "VAS 15 / IFRS 15",
		q: "Compare VAS 15 and IFRS 15 on revenue recognition from contracts with customers.",
	},
	{
		tag: "IFRS 2",
		q: "Explain the accounting treatment under IFRS 2 for equity-settled share-based awards.",
	},
	{
		tag: "IFRS 9",
		q: "How does IFRS 9 classify and measure financial assets? What changed from IAS 39?",
	},
];

function EmptyState({
	onSuggestion,
}: { onSuggestion: (text: string) => void }) {
	return (
		<div
			className="welcome"
			style={{
				flex: 1,
				display: "flex",
				flexDirection: "column",
				alignItems: "center",
			}}
		>
			<div className="welcome-eyebrow">VAS·IFRS</div>
			<h1 className="welcome-title">
				Knowledge <em>Engine</em>
			</h1>
			<p className="welcome-sub">
				Query Vietnamese Accounting Standards or IFRS. Answers grounded in
				retrieved source documents with citations.
			</p>
			<div className="welcome-cards">
				{SUGGESTIONS.map((s) => (
					<button
						key={s.tag}
						type="button"
						className="welcome-card"
						onClick={() => onSuggestion(s.q)}
					>
						<div className="welcome-card-tag">{s.tag}</div>
						<div className="welcome-card-q">{s.q}</div>
						<div className="welcome-card-foot">
							<span>Ask this →</span>
						</div>
					</button>
				))}
			</div>
		</div>
	);
}

/* ── Sources section ── */
function SourceRow({ citation, index }: { citation: Citation; index: number }) {
	const score = MOCK_RETRIEVAL_SCORES[index] ?? 0.55;
	const page = citation.chunk_id.split("-").pop() ?? "–";
	return (
		<div className="msg-source-row">
			<span className="msg-source-num">{index + 1}</span>
			<div style={{ flex: 1, minWidth: 0 }}>
				<div className="msg-source-title">
					{citation.doc_id}
					<small>p.{page}</small>
				</div>
			</div>
			<span className="msg-source-score">{score.toFixed(2)}</span>
			<ExternalLinkIcon />
		</div>
	);
}

function SourcesSection({ citations }: { citations: Citation[] }) {
	const [expanded, setExpanded] = useState(false);
	if (citations.length === 0) return null;
	return (
		<div className="msg-sources">
			<div className="msg-sources-hd">
				<span>References</span>
				<span style={{ color: "var(--accent)", fontWeight: 600 }}>
					§{citations.length}
				</span>
			</div>
			<div className="msg-sources-list">
				{citations.slice(0, expanded ? undefined : 3).map((c, i) => (
					<SourceRow key={c.key} citation={c} index={i} />
				))}
			</div>
			{citations.length > 3 && (
				<button
					type="button"
					onClick={() => setExpanded((v) => !v)}
					style={{
						marginTop: 6,
						fontSize: "0.7rem",
						fontWeight: 500,
						fontFamily: "var(--font-mono)",
						color: "var(--accent)",
						background: "transparent",
						border: "none",
						cursor: "pointer",
						padding: 0,
					}}
				>
					{expanded
						? "↑ Collapse"
						: `↓ Show all ${citations.length} references`}
				</button>
			)}
		</div>
	);
}

/* ── Message actions ── */
function MessageActions() {
	return (
		<div className="msg-actions">
			{(
				[
					{ icon: <CopyIcon />, title: "Copy" },
					{ icon: <ThumbUpIcon />, title: "Helpful" },
					{ icon: <ThumbDownIcon />, title: "Not helpful" },
					{ icon: <RegenerateIcon />, title: "Regenerate" },
				] as const
			).map(({ icon, title }) => (
				<button key={title} type="button" title={title} className="msg-act">
					{icon}
				</button>
			))}
		</div>
	);
}

/* ── Single message ── */
function MessageBubble({ msg }: { msg: Message }) {
	const isStreaming = msg.loading && msg.content.length > 0;

	if (msg.role === "user") {
		return (
			<div className="msg-user">
				<p
					style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}
				>
					{msg.content}
				</p>
			</div>
		);
	}

	return (
		<div className="msg-assistant">
			<div className="msg-meta">
				<span className="msg-meta-dot" />
				<span>Knowledge Engine</span>
				{msg.citations.length > 0 && (
					<>
						<span className="msg-meta-sep">·</span>
						<span style={{ color: "var(--accent)", fontWeight: 600 }}>
							§{msg.citations.length}
						</span>
					</>
				)}
			</div>

			{msg.loading && !msg.content ? (
				<div
					style={{
						display: "flex",
						gap: 5,
						alignItems: "center",
						paddingTop: 4,
					}}
				>
					{[0, 1, 2].map((i) => (
						<span
							key={i}
							style={{
								width: 5,
								height: 5,
								borderRadius: "50%",
								background: "var(--muted)",
								display: "inline-block",
								animation: "dot-bounce 1.2s infinite ease-in-out",
								animationDelay: `${i * 0.22}s`,
							}}
						/>
					))}
				</div>
			) : (
				<div className="msg-body">
					<span style={{ whiteSpace: "pre-wrap" }}>
						{msg.content}
						{isStreaming && (
							<span
								style={{
									display: "inline-block",
									width: 2,
									height: "1em",
									background: "var(--accent)",
									marginLeft: 1,
									verticalAlign: "text-bottom",
									animation: "cursor-blink 1s step-end infinite",
								}}
							/>
						)}
					</span>
				</div>
			)}

			{!msg.loading && <MessageActions />}
			{!msg.loading && <SourcesSection citations={msg.citations} />}
		</div>
	);
}

/* ── Public ── */
export interface MessageListProps {
	messages: Message[];
	onSuggestion?: (text: string) => void;
}

export function MessageList({ messages, onSuggestion }: MessageListProps) {
	const bottomRef = useRef<HTMLDivElement>(null);

	useEffect(() => {
		bottomRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [messages]);

	if (messages.length === 0) {
		return <EmptyState onSuggestion={onSuggestion ?? (() => {})} />;
	}

	return (
		<div style={{ flex: 1, overflowY: "auto" }}>
			<div
				className="thread"
				style={{ maxWidth: 760, margin: "0 auto", padding: "32px 32px 16px" }}
			>
				{messages.map((msg) => (
					<MessageBubble key={msg.id} msg={msg} />
				))}
				<div ref={bottomRef} />
			</div>
		</div>
	);
}
