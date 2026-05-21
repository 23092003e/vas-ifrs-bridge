"use client";

import { useState } from "react";

const STANDARDS = [
	{
		vas: "VAS 01 — Chuẩn mực chung",
		ifrs: "Conceptual Framework",
		status: "Partial alignment",
		diff: "Differences in measurement basis and qualitative characteristics",
	},
	{
		vas: "VAS 14 — Doanh thu & Thu nhập khác",
		ifrs: "IFRS 15 — Revenue from Contracts",
		status: "Significant difference",
		diff: "5-step model vs. recognition when risks/rewards transferred",
	},
	{
		vas: "VAS 15 — Hợp đồng xây dựng",
		ifrs: "IFRS 15 — Revenue from Contracts",
		status: "Partially superseded",
		diff: "VAS 15 uses percentage-of-completion; IFRS 15 uses performance obligations",
	},
	{
		vas: "VAS 17 — Thuế Thu nhập Doanh nghiệp",
		ifrs: "IAS 12 — Income Taxes",
		status: "Broadly aligned",
		diff: "Minor differences in deferred tax recognition thresholds",
	},
	{
		vas: "VAS 21 — Trình bày Báo cáo Tài chính",
		ifrs: "IAS 1 — Presentation of Financial Statements",
		status: "Significant difference",
		diff: "VAS has prescribed formats; IAS 1 allows flexibility",
	},
];

const FILTERS = [
	"All",
	"Significant difference",
	"Partial alignment",
	"Broadly aligned",
] as const;
type Filter = (typeof FILTERS)[number];

function statusColor(s: string) {
	if (s === "Broadly aligned") return "var(--score-high)";
	if (s.includes("Partial")) return "var(--score-mid)";
	return "var(--score-low)";
}

function matchesFilter(status: string, filter: Filter): boolean {
	if (filter === "All") return true;
	if (filter === "Partial alignment") return status.includes("Partial");
	return status === filter;
}

export default function ComparePage() {
	const [activeFilter, setActiveFilter] = useState<Filter>("All");

	const visible = STANDARDS.filter((s) =>
		matchesFilter(s.status, activeFilter),
	);

	return (
		<div style={{ flex: 1, overflow: "auto", background: "var(--chat-bg)" }}>
			<div
				style={{
					padding: "24px 32px 16px",
					borderBottom: "1px solid var(--rule)",
					background: "var(--surface)",
				}}
			>
				<div
					style={{
						width: 32,
						height: 2,
						background: "var(--accent)",
						marginBottom: 12,
					}}
				/>
				<h1
					style={{
						margin: "0 0 4px",
						fontFamily: "var(--font-lora, Georgia, serif)",
						fontSize: "1.375rem",
						fontWeight: 700,
						color: "var(--ink)",
						letterSpacing: "-0.01em",
					}}
				>
					VAS ↔ IFRS Comparison
				</h1>
				<p
					style={{
						margin: 0,
						fontSize: "0.82rem",
						fontStyle: "italic",
						fontFamily: "var(--font-lora, Georgia, serif)",
						color: "var(--ink-40)",
					}}
				>
					Alignment analysis of Vietnamese Accounting Standards and
					International Financial Reporting Standards
				</p>
			</div>

			<div
				style={{
					padding: "12px 32px",
					borderBottom: "1px solid var(--rule)",
					background: "var(--paper-alt)",
					display: "flex",
					alignItems: "center",
					gap: 8,
				}}
			>
				<span
					style={{
						fontSize: "0.65rem",
						fontFamily: "var(--font-mono)",
						color: "var(--ink-40)",
						letterSpacing: "0.06em",
					}}
				>
					FILTER:
				</span>
				{FILTERS.map((f) => {
					const isActive = f === activeFilter;
					return (
						<button
							key={f}
							type="button"
							onClick={() => setActiveFilter(f)}
							style={{
								padding: "3px 10px",
								borderRadius: 3,
								fontSize: "0.68rem",
								fontFamily: "var(--font-mono)",
								border: isActive
									? "1px solid var(--accent)"
									: "1px solid var(--rule)",
								background: isActive ? "var(--accent)" : "transparent",
								color: isActive ? "#fff" : "var(--ink-60)",
								cursor: "pointer",
								transition:
									"background 120ms ease, border-color 120ms ease, color 120ms ease",
							}}
						>
							{f}
						</button>
					);
				})}
				{activeFilter !== "All" && (
					<span
						style={{
							fontSize: "0.63rem",
							fontFamily: "var(--font-mono)",
							color: "var(--ink-40)",
							marginLeft: 4,
						}}
					>
						{visible.length} of {STANDARDS.length}
					</span>
				)}
			</div>

			<div style={{ padding: "24px 32px" }}>
				<table style={{ width: "100%", borderCollapse: "collapse" }}>
					<thead>
						<tr style={{ borderBottom: "2px solid var(--ink)" }}>
							{[
								"VAS Standard",
								"IFRS / IAS Equivalent",
								"Alignment",
								"Key Difference",
							].map((h) => (
								<th
									key={h}
									style={{
										padding: "8px 12px",
										textAlign: "left",
										fontSize: "0.62rem",
										fontFamily: "var(--font-mono)",
										fontWeight: 700,
										color: "var(--ink-60)",
										letterSpacing: "0.06em",
										textTransform: "uppercase",
									}}
								>
									{h}
								</th>
							))}
						</tr>
					</thead>
					<tbody>
						{visible.map((s, i) => (
							<tr
								key={i}
								className="compare-row"
								style={{ borderBottom: "1px solid var(--rule)" }}
							>
								<td style={{ padding: "12px 12px", verticalAlign: "top" }}>
									<span
										style={{
											fontSize: "0.8rem",
											fontWeight: 600,
											fontFamily: "var(--font-lora, Georgia, serif)",
											color: "var(--ink)",
										}}
									>
										{s.vas}
									</span>
								</td>
								<td style={{ padding: "12px 12px", verticalAlign: "top" }}>
									<span
										style={{
											fontSize: "0.8rem",
											fontFamily: "var(--font-lora, Georgia, serif)",
											color: "var(--ink)",
										}}
									>
										{s.ifrs}
									</span>
								</td>
								<td
									style={{
										padding: "12px 12px",
										verticalAlign: "top",
										whiteSpace: "nowrap",
									}}
								>
									<span
										style={{
											fontSize: "0.67rem",
											fontFamily: "var(--font-mono)",
											fontWeight: 700,
											color: statusColor(s.status),
										}}
									>
										{s.status}
									</span>
								</td>
								<td style={{ padding: "12px 12px", verticalAlign: "top" }}>
									<span
										style={{
											fontSize: "0.78rem",
											fontStyle: "italic",
											fontFamily: "var(--font-lora, Georgia, serif)",
											color: "var(--ink-60)",
										}}
									>
										{s.diff}
									</span>
								</td>
							</tr>
						))}
						{visible.length === 0 && (
							<tr>
								<td
									colSpan={4}
									style={{
										padding: "32px 12px",
										textAlign: "center",
										fontSize: "0.82rem",
										fontStyle: "italic",
										fontFamily: "var(--font-lora, Georgia, serif)",
										color: "var(--ink-40)",
									}}
								>
									No standards match this filter.
								</td>
							</tr>
						)}
					</tbody>
				</table>
			</div>
		</div>
	);
}
