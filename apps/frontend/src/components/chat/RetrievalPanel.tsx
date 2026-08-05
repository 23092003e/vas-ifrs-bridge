"use client";

import type { Citation, Message } from "@/types/api";

function CloseIcon() {
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
			<line x1="18" y1="6" x2="6" y2="18" />
			<line x1="6" y1="6" x2="18" y2="18" />
		</svg>
	);
}

function ChunkCard({ citation, index }: { citation: Citation; index: number }) {
	const page = citation.chunk_id.split("-").pop() ?? "–";
	const excerpt = citation.snippet.slice(0, 140);

	return (
		<div className="chunk">
			<div className="chunk-hd">
				<div className="chunk-num">{index + 1}</div>
				<div className="chunk-doc">
					{citation.doc_id}
					<small>p.{page}</small>
				</div>
				{citation.standard_code && (
					<div className="chunk-score">{citation.standard_code}</div>
				)}
			</div>
			<p className="chunk-excerpt">
				{excerpt}
				{citation.snippet.length > excerpt.length ? "…" : ""}
			</p>
		</div>
	);
}

export interface RetrievalPanelProps {
	messages: Message[];
	onClose?: () => void;
}

export function RetrievalPanel({ messages, onClose }: RetrievalPanelProps) {
	const lastAssistant = messages.findLast(
		(message) => message.role === "assistant" && !message.loading,
	);
	const citations = lastAssistant?.citations ?? [];

	return (
		<aside className="drawer" data-open="true" aria-label="Retrieved sources">
			<div className="drawer-hd">
				<span className="drawer-hd-title">Retrieved Sources</span>
				<div className="drawer-hd-actions">
					<button
						type="button"
						onClick={onClose}
						className="topbar-iconbtn"
						title="Close sources"
						aria-label="Close sources"
					>
						<CloseIcon />
					</button>
				</div>
			</div>

			<div className="drawer-body">
				{citations.length === 0 ? (
					<div className="drawer-empty">
						<div className="drawer-empty-icon">◈</div>
						<p>No sources yet. Submit a query to inspect citations.</p>
					</div>
				) : (
					citations.map((citation, index) => (
						<ChunkCard
							key={`${citation.key}:${citation.chunk_id}`}
							citation={citation}
							index={index}
						/>
					))
				)}
			</div>
		</aside>
	);
}
