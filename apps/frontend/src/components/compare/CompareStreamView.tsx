"use client";

import type { Citation } from "@/types/api";
import Link from "next/link";
import { useState } from "react";

interface CompareStreamViewProps {
	vasCode: string;
	ifrsCode: string;
	content: string;
	citations: Citation[];
	loading: boolean;
	error: string | null;
	onRetry?: () => void;
}

export function CompareStreamView({
	vasCode,
	ifrsCode,
	content,
	citations,
	loading,
	error,
	onRetry,
}: CompareStreamViewProps) {
	const [copied, setCopied] = useState(false);
	const [expandedCitations, setExpandedCitations] = useState(false);
	const [activeCitationKey, setActiveCitationKey] = useState<string | null>(
		null,
	);

	const handleCopy = async () => {
		if (!content) return;
		try {
			await navigator.clipboard.writeText(content);
			setCopied(true);
			setTimeout(() => setCopied(false), 2000);
		} catch (err) {
			console.error("Failed to copy comparison text", err);
		}
	};

	const handleDownloadMarkdown = () => {
		if (!content) return;
		const filename = `VAS_IFRS_Compare_${vasCode}_${ifrsCode}.md`.replace(
			/[^\w.-]/g,
			"_",
		);
		const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = filename;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	};

	if (!content && !loading && !error) {
		return (
			<div
				style={{
					background: "var(--surface)",
					border: "1.5px dashed var(--border)",
					borderRadius: 8,
					padding: "48px 32px",
					textAlign: "center",
				}}
			>
				<div
					style={{
						fontSize: "2rem",
						marginBottom: 12,
						color: "var(--muted)",
					}}
				>
					⚖️
				</div>
				<h3
					style={{
						fontFamily: "var(--font-serif)",
						fontSize: "1.1rem",
						margin: "0 0 8px",
						color: "var(--ink)",
					}}
				>
					Sẵn sàng đối chiếu chuẩn mực
				</h3>
				<p
					style={{
						fontSize: "0.82rem",
						color: "var(--muted)",
						maxWidth: 500,
						margin: "0 auto",
						lineHeight: 1.6,
					}}
				>
					Chọn một cặp chuẩn mực hoặc bấm vào một trong các chủ đề gợi ý phía
					trên, sau đó nhấn <strong>So sánh ngay (AI RAG)</strong> để nhận phân
					tích chi tiết kèm trích dẫn văn bản quy phạm.
				</p>
			</div>
		);
	}

	return (
		<div
			style={{
				background: "var(--surface)",
				border: "1px solid var(--border)",
				borderRadius: 8,
				boxShadow: "var(--shadow-sm)",
				overflow: "hidden",
			}}
		>
			{/* Top Header of Result */}
			<div
				style={{
					padding: "16px 20px",
					borderBottom: "1px solid var(--border)",
					background: "var(--surface-2)",
					display: "flex",
					alignItems: "center",
					justifyContent: "space-between",
					flexWrap: "wrap",
					gap: 12,
				}}
			>
				<div style={{ display: "flex", alignItems: "center", gap: 10 }}>
					<span
						style={{
							fontSize: "0.95rem",
							fontWeight: 700,
							color: "var(--ink)",
							fontFamily: "var(--font-sans)",
						}}
					>
						Đối chiếu: {vasCode} ⇄ {ifrsCode}
					</span>
					{loading && (
						<span
							style={{
								display: "inline-flex",
								alignItems: "center",
								gap: 6,
								fontSize: "0.72rem",
								fontFamily: "var(--font-mono)",
								color: "var(--accent)",
								fontWeight: 600,
							}}
						>
							<span
								style={{
									width: 6,
									height: 6,
									borderRadius: "50%",
									background: "var(--accent)",
									animation: "cursor-blink 0.8s infinite",
								}}
							/>
							Đang tổng hợp...
						</span>
					)}
				</div>

				{/* Utility Actions */}
				<div style={{ display: "flex", alignItems: "center", gap: 8 }}>
					<button
						type="button"
						onClick={handleCopy}
						disabled={!content}
						style={{
							padding: "5px 10px",
							fontSize: "0.72rem",
							fontFamily: "var(--font-mono)",
							background: "var(--surface)",
							border: "1px solid var(--border)",
							borderRadius: 4,
							color: copied ? "var(--success)" : "var(--ink-2)",
							cursor: content ? "pointer" : "not-allowed",
							display: "inline-flex",
							alignItems: "center",
							gap: 4,
						}}
					>
						{copied ? "✓ Đã chép!" : "📋 Sao chép"}
					</button>

					<button
						type="button"
						onClick={handleDownloadMarkdown}
						disabled={!content}
						style={{
							padding: "5px 10px",
							fontSize: "0.72rem",
							fontFamily: "var(--font-mono)",
							background: "var(--surface)",
							border: "1px solid var(--border)",
							borderRadius: 4,
							color: "var(--ink-2)",
							cursor: content ? "pointer" : "not-allowed",
							display: "inline-flex",
							alignItems: "center",
							gap: 4,
						}}
					>
						📥 Xuất .md
					</button>

					<Link
						href={`/chat?q=${encodeURIComponent(
							`So sánh chuẩn mực ${vasCode} và ${ifrsCode}`,
						)}`}
						style={{
							padding: "5px 10px",
							fontSize: "0.72rem",
							fontFamily: "var(--font-mono)",
							background: "var(--surface)",
							border: "1px solid var(--border)",
							borderRadius: 4,
							color: "var(--accent)",
							textDecoration: "none",
							display: "inline-flex",
							alignItems: "center",
							gap: 4,
						}}
					>
						💬 Mở trong Chat
					</Link>
				</div>
			</div>

			{/* Error Box if any */}
			{error && (
				<div
					style={{
						padding: "12px 20px",
						background: "#fef2f2",
						borderBottom: "1px solid #fecaca",
						color: "#991b1b",
						fontSize: "0.8rem",
						fontFamily: "var(--font-mono)",
						display: "flex",
						alignItems: "center",
						justifyContent: "space-between",
					}}
				>
					<span>Lỗi: {error}</span>
					{onRetry && (
						<button
							type="button"
							onClick={onRetry}
							style={{
								border: "none",
								background: "none",
								color: "#dc2626",
								fontWeight: 700,
								cursor: "pointer",
								textDecoration: "underline",
							}}
						>
							Thử lại
						</button>
					)}
				</div>
			)}

			{/* Content Area */}
			<div
				style={{
					padding: "24px 28px",
					fontSize: "0.88rem",
					lineHeight: 1.7,
					color: "var(--ink)",
					fontFamily: "var(--font-sans)",
				}}
			>
				{loading && !content ? (
					<div
						style={{
							display: "flex",
							flexDirection: "column",
							gap: 12,
							padding: "20px 0",
						}}
					>
						<div
							style={{
								height: 16,
								width: "40%",
								background: "var(--surface-2)",
								borderRadius: 4,
							}}
						/>
						<div
							style={{
								height: 14,
								width: "90%",
								background: "var(--surface-2)",
								borderRadius: 4,
							}}
						/>
						<div
							style={{
								height: 14,
								width: "80%",
								background: "var(--surface-2)",
								borderRadius: 4,
							}}
						/>
						<div
							style={{
								height: 14,
								width: "60%",
								background: "var(--surface-2)",
								borderRadius: 4,
							}}
						/>
					</div>
				) : (
					<div style={{ whiteSpace: "pre-wrap" }}>
						{content.split(/(\[C\d+(?:[,\s]+C\d+)*\])/g).map((part, i) => {
							if (part.startsWith("[C") && part.endsWith("]")) {
								const keys = part.match(/C\d+/g) || [];
								return (
									<span
										key={i}
										className="msg-inline-citations"
										style={{ whiteSpace: "normal" }}
									>
										{keys.map((key, j) => {
											const index = citations.findIndex((c) => c.key === key);
											if (index === -1) return null;
											const citation = citations[index];
											const isActive = activeCitationKey === key;
											return (
												<button
													type="button"
													key={j}
													onClick={() => {
														setActiveCitationKey(isActive ? null : key);
														setExpandedCitations(true);
													}}
													title={`${citation.doc_id}: ${citation.snippet.slice(0, 100)}...`}
													style={{
														display: "inline-flex",
														alignItems: "center",
														justifyContent: "center",
														background: isActive
															? "var(--ink)"
															: "var(--accent)",
														color: "white",
														fontSize: "0.7em",
														fontWeight: 700,
														padding: "0 5px",
														borderRadius: 4,
														margin: "0 2px",
														verticalAlign: "super",
														cursor: "pointer",
														minWidth: 16,
														height: 16,
														border: "none",
													}}
												>
													{index + 1}
												</button>
											);
										})}
									</span>
								);
							}
							return <span key={i}>{part}</span>;
						})}
						{loading && (
							<span
								style={{
									display: "inline-block",
									width: 3,
									height: "1em",
									background: "var(--accent)",
									marginLeft: 2,
									verticalAlign: "text-bottom",
									animation: "cursor-blink 1s step-end infinite",
								}}
							/>
						)}
					</div>
				)}
			</div>

			{/* Citations & Evidence Section */}
			{citations.length > 0 && (
				<div
					style={{
						padding: "16px 20px",
						borderTop: "1px solid var(--border)",
						background: "var(--surface-2)",
					}}
				>
					<div
						style={{
							display: "flex",
							alignItems: "center",
							justifyContent: "space-between",
							cursor: "pointer",
						}}
						onClick={() => setExpandedCitations((prev) => !prev)}
					>
						<div style={{ display: "flex", alignItems: "center", gap: 8 }}>
							<span
								style={{
									fontSize: "0.72rem",
									fontFamily: "var(--font-mono)",
									fontWeight: 700,
									color: "var(--muted)",
									textTransform: "uppercase",
									letterSpacing: "0.06em",
								}}
							>
								Trích dẫn & Nguồn căn cứ ({citations.length})
							</span>
							<span
								style={{
									fontSize: "0.68rem",
									fontFamily: "var(--font-mono)",
									color: "var(--accent)",
									fontWeight: 600,
								}}
							>
								§{citations.length} nguồn văn bản
							</span>
						</div>
						<span
							style={{
								fontSize: "0.75rem",
								color: "var(--muted)",
							}}
						>
							{expandedCitations ? "▲ Thu gọn" : "▼ Xem chi tiết"}
						</span>
					</div>

					{expandedCitations && (
						<div
							style={{
								marginTop: 12,
								display: "flex",
								flexDirection: "column",
								gap: 8,
							}}
						>
							{citations.map((c, idx) => {
								const isActive = activeCitationKey === c.key;
								return (
									<div
										key={c.key}
										style={{
											padding: "10px 14px",
											borderRadius: 6,
											background: isActive
												? "var(--surface)"
												: "var(--surface-3)",
											border: isActive
												? "1.5px solid var(--accent)"
												: "1px solid var(--border)",
											fontSize: "0.78rem",
										}}
									>
										<div
											style={{
												display: "flex",
												alignItems: "center",
												justifyContent: "space-between",
												marginBottom: 4,
											}}
										>
											<div
												style={{
													display: "flex",
													alignItems: "center",
													gap: 8,
												}}
											>
												<span
													style={{
														fontSize: "0.7rem",
														fontFamily: "var(--font-mono)",
														fontWeight: 700,
														padding: "1px 6px",
														borderRadius: 3,
														background: "var(--accent)",
														color: "#fff",
													}}
												>
													[{idx + 1}]
												</span>
												<span
													style={{
														fontFamily: "var(--font-mono)",
														fontWeight: 600,
														color: "var(--ink)",
													}}
												>
													{c.doc_id}
												</span>
											</div>
											{c.standard_code && (
												<span
													style={{
														fontFamily: "var(--font-mono)",
														fontSize: "0.68rem",
														color: "var(--muted)",
													}}
												>
													{c.standard_code}
												</span>
											)}
										</div>
										<p
											style={{
												margin: 0,
												color: "var(--ink-2)",
												lineHeight: 1.5,
												fontStyle: "italic",
											}}
										>
											&ldquo;{c.snippet}&rdquo;
										</p>
									</div>
								);
							})}
						</div>
					)}
				</div>
			)}
		</div>
	);
}
