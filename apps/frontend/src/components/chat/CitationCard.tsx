"use client";

import type { Citation } from "@/types/api";

/* Kept for backwards compatibility — rendering is now done via SourceRow in MessageList */
export function CitationCard({ citation }: { citation: Citation }) {
	const ext = citation.doc_id.split(".").pop()?.toLowerCase() ?? "pdf";
	const docColor =
		ext === "pdf" ? "#ef4444" : ext === "docx" ? "#3b82f6" : "#6b7280";
	const page = citation.chunk_id.split("-").pop() ?? "–";

	return (
		<div
			className="rounded-xl overflow-hidden"
			style={{
				border: "1px solid var(--chat-border)",
				background: "var(--chat-surface)",
				minWidth: 200,
				maxWidth: 260,
				flexShrink: 0,
			}}
		>
			<div className="px-3 py-2.5">
				<div className="flex items-center gap-1.5 mb-1">
					<svg
						width="13"
						height="13"
						viewBox="0 0 24 24"
						fill="none"
						stroke={docColor}
						strokeWidth="2"
						strokeLinecap="round"
						strokeLinejoin="round"
					>
						<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
						<polyline points="14 2 14 8 20 8" />
					</svg>
					<span
						className="text-xs font-semibold truncate"
						style={{ color: "var(--chat-text)" }}
					>
						{citation.doc_id}
					</span>
				</div>
				<p className="text-xs" style={{ color: "var(--chat-text-muted)" }}>
					Page {page}
				</p>
				{citation.standard_code && (
					<span
						className="inline-block mt-1 rounded-md px-1.5 py-0.5 text-xs font-semibold"
						style={{
							background: citation.standard_code.startsWith("IFRS")
								? "#ebf5ff"
								: "#f3faf7",
							color: citation.standard_code.startsWith("IFRS")
								? "#1e429f"
								: "#03543f",
							border: `1px solid ${citation.standard_code.startsWith("IFRS") ? "#bfdbfe" : "#a7f3d0"}`,
						}}
					>
						{citation.standard_code}
					</span>
				)}
				<p
					className="text-xs leading-relaxed mt-1.5 line-clamp-3"
					style={{ color: "var(--chat-text-muted)" }}
				>
					{citation.snippet.slice(0, 120)}...
				</p>
			</div>
		</div>
	);
}
