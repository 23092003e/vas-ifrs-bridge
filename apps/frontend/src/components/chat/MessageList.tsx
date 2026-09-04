"use client";

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
/* ── Empty / welcome state ── */
/* ── Empty / welcome state ── */
interface SuggestionCard {
	tag: string;
	title: string;
	category: string;
	q: string;
	detail: string;
}

const SUGGESTIONS: SuggestionCard[] = [
	{
		tag: "IFRS 16 · VAS 06",
		title: "Thuê tài sản hoạt động 5 năm",
		category: "ROU Asset & Lease Liability",
		q: "Phân tích khác biệt chính giữa IFRS 16 và VAS 06 đối với hợp đồng thuê văn phòng 5 năm?",
		detail:
			"Đánh giá tác động ghi nhận Quyền sử dụng tài sản (ROU) và Nợ phải trả thuê tài sản lên EBITDA & Đòn bẩy tài chính.",
	},
	{
		tag: "IFRS 15 · VAS 14",
		title: "Nghĩa vụ thực hiện hợp đồng",
		category: "Doanh thu 5 bước",
		q: "Cách xác định Nghĩa vụ thực hiện riêng biệt (Performance Obligations) theo IFRS 15?",
		detail:
			"Phương pháp phân bổ giá giao dịch và thời điểm ghi nhận quyền kiểm soát hàng hóa kèm dịch vụ bảo hành/bảo trì.",
	},
	{
		tag: "IFRS 9 · TT 48",
		title: "Tổn thất tín dụng dự kiến (ECL)",
		category: "Công cụ tài chính",
		q: "Bút toán điều chỉnh trích lập dự phòng tổn thất tín dụng theo IFRS 9 thay vì Thông tư 48?",
		detail:
			"Chuyển dịch từ mô hình tổn thất đã phát sinh (Incurred Loss) sang mô hình tổn thất dự kiến 3 giai đoạn (Staging ECL).",
	},
	{
		tag: "IAS 12 · VAS 17",
		title: "Tài sản thuế hoãn lại",
		category: "Thuế thu nhập doanh nghiệp",
		q: "Xác định tài sản thuế hoãn lại đối với chênh lệch tạm thời theo IAS 12 vs VAS 17?",
		detail:
			"Nguyên tắc ghi nhận theo phương pháp Bảng cân đối (Balance Sheet Liability) đối với các khoản chênh lệch khấu trừ.",
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
				padding: "36px 20px 24px",
				maxWidth: 820,
				margin: "0 auto",
				width: "100%",
			}}
		>
			<div
				style={{
					display: "inline-flex",
					alignItems: "center",
					gap: 8,
					padding: "4px 12px",
					borderRadius: "999px",
					background: "var(--surface-2)",
					border: "1px solid var(--border)",
					fontSize: "0.7rem",
					fontFamily: "var(--font-mono)",
					color: "var(--accent-ink)",
					marginBottom: 16,
					letterSpacing: "0.06em",
					textTransform: "uppercase",
				}}
			>
				<span
					style={{
						width: 6,
						height: 6,
						borderRadius: "50%",
						background: "var(--success)",
						boxShadow: "0 0 6px var(--success)",
					}}
				/>
				<span>Grounded Audit Engine · RAG & Knowledge Graph</span>
			</div>

			<h1
				style={{
					fontFamily: "var(--font-serif)",
					fontSize: "clamp(1.75rem, 3.5vw, 2.3rem)",
					fontWeight: 500,
					letterSpacing: "-0.02em",
					lineHeight: 1.15,
					color: "var(--ink)",
					textAlign: "center",
					margin: "0 0 10px",
				}}
			>
				Hệ thống Trợ lý Chuẩn mực <em>VAS & IFRS</em>
			</h1>

			<p
				style={{
					fontSize: "0.86rem",
					color: "var(--muted)",
					textAlign: "center",
					maxWidth: 620,
					margin: "0 auto 20px",
					lineHeight: 1.6,
				}}
			>
				Tra cứu, đối chiếu và đề xuất bút toán chuyển đổi báo cáo tài chính. Mọi
				câu trả lời đều được kiểm chứng chéo với số đoạn chuẩn mực, thông tư và
				tài liệu dẫn chứng cụ thể.
			</p>

			{/* Quick metadata strip */}
			<div
				style={{
					display: "flex",
					flexWrap: "wrap",
					justifyContent: "center",
					gap: "8px 16px",
					padding: "8px 16px",
					borderRadius: "var(--radius)",
					background: "var(--surface-2)",
					border: "1px solid var(--border)",
					fontSize: "0.72rem",
					fontFamily: "var(--font-mono)",
					color: "var(--ink-2)",
					marginBottom: 28,
				}}
			>
				<span>
					<strong style={{ color: "var(--ink)" }}>26</strong> VAS Standards
				</span>
				<span style={{ color: "var(--faint)" }}>•</span>
				<span>
					<strong style={{ color: "var(--ink)" }}>41</strong> IFRS/IAS Rules
				</span>
				<span style={{ color: "var(--faint)" }}>•</span>
				<span>
					<strong style={{ color: "var(--ink)" }}>200+</strong> Ontology
					Mappings
				</span>
				<span style={{ color: "var(--faint)" }}>•</span>
				<span style={{ color: "var(--accent)" }}>Zero Data Training</span>
			</div>

			{/* 4 Business scenario prompt chips */}
			<div
				style={{
					display: "grid",
					gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
					gap: 12,
					width: "100%",
				}}
			>
				{SUGGESTIONS.map((s) => (
					<button
						key={s.tag}
						type="button"
						onClick={() => onSuggestion(s.q)}
						style={{
							textAlign: "left",
							background: "var(--surface)",
							border: "1px solid var(--border)",
							borderRadius: "var(--radius-lg)",
							padding: "14px 16px",
							cursor: "pointer",
							transition: "all 150ms cubic-bezier(0.16, 1, 0.3, 1)",
							display: "flex",
							flexDirection: "column",
							gap: 6,
							position: "relative",
						}}
						onMouseEnter={(e) => {
							e.currentTarget.style.borderColor = "var(--accent)";
							e.currentTarget.style.boxShadow =
								"0 2px 12px rgba(0,0,0,0.06), 0 0 0 1px var(--accent-ring)";
							e.currentTarget.style.transform = "translateY(-1px)";
						}}
						onMouseLeave={(e) => {
							e.currentTarget.style.borderColor = "var(--border)";
							e.currentTarget.style.boxShadow = "none";
							e.currentTarget.style.transform = "none";
						}}
					>
						<div
							style={{
								display: "flex",
								alignItems: "center",
								justifyContent: "space-between",
								gap: 8,
							}}
						>
							<span
								style={{
									fontFamily: "var(--font-mono)",
									fontSize: "0.68rem",
									fontWeight: 600,
									color: "var(--accent-ink)",
									background: "var(--accent-soft)",
									padding: "2px 7px",
									borderRadius: "4px",
									letterSpacing: "0.02em",
								}}
							>
								{s.tag}
							</span>
							<span
								style={{
									fontFamily: "var(--font-mono)",
									fontSize: "0.64rem",
									color: "var(--muted)",
									textTransform: "uppercase",
								}}
							>
								{s.category}
							</span>
						</div>

						<div
							style={{
								fontSize: "0.85rem",
								fontWeight: 600,
								color: "var(--ink)",
								lineHeight: 1.35,
								marginTop: 2,
							}}
						>
							{s.q}
						</div>

						<p
							style={{
								margin: 0,
								fontSize: "0.74rem",
								color: "var(--muted)",
								lineHeight: 1.45,
							}}
						>
							{s.detail}
						</p>

						<div
							style={{
								marginTop: 4,
								display: "flex",
								alignItems: "center",
								justifyContent: "flex-end",
								fontSize: "0.7rem",
								fontFamily: "var(--font-mono)",
								fontWeight: 500,
								color: "var(--accent)",
								gap: 4,
							}}
						>
							<span>Phân tích nghiệp vụ</span>
							<span>→</span>
						</div>
					</button>
				))}
			</div>
		</div>
	);
}

/* ── Sources section ── */
function SourceRow({ citation, index }: { citation: Citation; index: number }) {
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
			{citation.standard_code && (
				<span className="msg-source-score">{citation.standard_code}</span>
			)}
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
						{msg.content.split(/(\[C\d+(?:[,\s]+C\d+)*\])/g).map((part, i) => {
							if (part.startsWith("[C") && part.endsWith("]")) {
								const keys = part.match(/C\d+/g) || [];
								return (
									<span
										key={i}
										className="msg-inline-citations"
										style={{ whiteSpace: "normal" }}
									>
										{keys.map((key, j) => {
											const index = msg.citations.findIndex(
												(c) => c.key === key,
											);
											if (index === -1) return null;
											return (
												<span
													key={j}
													title={msg.citations[index].doc_id}
													style={{
														display: "inline-flex",
														alignItems: "center",
														justifyContent: "center",
														background: "var(--accent)",
														color: "white",
														fontSize: "0.75em",
														fontWeight: 600,
														padding: "0 4px",
														borderRadius: "4px",
														margin: "0 2px",
														verticalAlign: "super",
														cursor: "pointer",
														minWidth: "16px",
														height: "16px",
													}}
												>
													{index + 1}
												</span>
											);
										})}
									</span>
								);
							}
							return <span key={i}>{part}</span>;
						})}
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
