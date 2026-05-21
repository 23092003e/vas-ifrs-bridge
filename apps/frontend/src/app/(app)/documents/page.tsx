"use client";

export default function DocumentsPage() {
	const docs = [
		{
			name: "IFRS_Standards_2024_Consolidated.pdf",
			type: "pdf",
			size: "12.4 MB",
			status: "Indexed",
			chunks: 4820,
			date: "2025-03-01",
		},
		{
			name: "VAS_Circulars_2021_2023.pdf",
			type: "pdf",
			size: "8.1 MB",
			status: "Indexed",
			chunks: 3140,
			date: "2025-03-01",
		},
		{
			name: "IAS_37_Provisions_Contingent.pdf",
			type: "pdf",
			size: "1.2 MB",
			status: "Indexed",
			chunks: 310,
			date: "2025-04-10",
		},
		{
			name: "IFRS_9_Financial_Instruments.pdf",
			type: "pdf",
			size: "2.8 MB",
			status: "Indexed",
			chunks: 890,
			date: "2025-04-10",
		},
		{
			name: "Audit_Report_Q1_2025.pdf",
			type: "pdf",
			size: "0.9 MB",
			status: "Processing",
			chunks: 0,
			date: "2025-05-18",
		},
		{
			name: "Internal_Accounting_Policy.docx",
			type: "docx",
			size: "0.4 MB",
			status: "Queued",
			chunks: 0,
			date: "2025-05-20",
		},
	];

	const statusColor = (s: string) =>
		s === "Indexed"
			? "var(--score-high)"
			: s === "Processing"
				? "var(--score-mid)"
				: "var(--ink-20)";

	return (
		<div style={{ flex: 1, overflow: "auto", background: "var(--chat-bg)" }}>
			<div
				style={{
					padding: "24px 32px 16px",
					borderBottom: "1px solid var(--rule)",
					background: "var(--surface)",
					display: "flex",
					alignItems: "flex-end",
					justifyContent: "space-between",
				}}
			>
				<div>
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
						Knowledge Base
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
						Source documents indexed for retrieval
					</p>
				</div>
				<button
					type="button"
					style={{
						padding: "8px 16px",
						borderRadius: 3,
						background: "var(--accent)",
						color: "#fff",
						border: "none",
						fontSize: "0.72rem",
						fontWeight: 700,
						fontFamily: "var(--font-mono)",
						letterSpacing: "0.05em",
						cursor: "pointer",
					}}
				>
					+ UPLOAD DOCUMENT
				</button>
			</div>

			<div
				style={{
					padding: "16px 32px",
					borderBottom: "1px solid var(--rule)",
					background: "var(--paper-alt)",
					display: "flex",
					gap: 40,
				}}
			>
				{[
					["Total Documents", "6"],
					["Total Chunks", "9,160"],
					["Indexed", "4"],
					["Storage Used", "25.8 MB"],
				].map(([l, v]) => (
					<div key={l}>
						<p
							style={{
								margin: "0 0 2px",
								fontSize: "0.6rem",
								fontFamily: "var(--font-mono)",
								color: "var(--ink-40)",
								letterSpacing: "0.06em",
								textTransform: "uppercase",
							}}
						>
							{l}
						</p>
						<p
							style={{
								margin: 0,
								fontSize: "1.125rem",
								fontWeight: 700,
								fontFamily: "var(--font-mono)",
								color: "var(--ink)",
							}}
						>
							{v}
						</p>
					</div>
				))}
			</div>

			<div style={{ padding: "24px 32px" }}>
				<table style={{ width: "100%", borderCollapse: "collapse" }}>
					<thead>
						<tr style={{ borderBottom: "2px solid var(--ink)" }}>
							{["Document", "Size", "Status", "Chunks", "Added"].map((h) => (
								<th
									key={h}
									style={{
										padding: "8px 12px",
										textAlign: "left",
										fontSize: "0.6rem",
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
						{docs.map((d, i) => (
							<tr
								key={i}
								style={{
									borderBottom: "1px solid var(--rule)",
									cursor: "pointer",
								}}
								onMouseEnter={(e) => {
									(e.currentTarget as HTMLElement).style.background =
										"var(--accent-light)";
								}}
								onMouseLeave={(e) => {
									(e.currentTarget as HTMLElement).style.background =
										"transparent";
								}}
							>
								<td style={{ padding: "11px 12px" }}>
									<div
										style={{ display: "flex", alignItems: "center", gap: 8 }}
									>
										<span
											style={{
												fontSize: "0.58rem",
												fontFamily: "var(--font-mono)",
												fontWeight: 700,
												padding: "1px 5px",
												borderRadius: 2,
												background: d.type === "pdf" ? "#fef2f2" : "#eff6ff",
												color: d.type === "pdf" ? "#dc2626" : "#2563eb",
											}}
										>
											{d.type.toUpperCase()}
										</span>
										<span
											style={{
												fontSize: "0.78rem",
												fontFamily: "var(--font-mono)",
												color: "var(--ink)",
											}}
										>
											{d.name}
										</span>
									</div>
								</td>
								<td
									style={{
										padding: "11px 12px",
										fontSize: "0.73rem",
										fontFamily: "var(--font-mono)",
										color: "var(--ink-40)",
									}}
								>
									{d.size}
								</td>
								<td style={{ padding: "11px 12px" }}>
									<span
										style={{
											fontSize: "0.65rem",
											fontFamily: "var(--font-mono)",
											fontWeight: 700,
											color: statusColor(d.status),
										}}
									>
										{d.status}
									</span>
								</td>
								<td
									style={{
										padding: "11px 12px",
										fontSize: "0.73rem",
										fontFamily: "var(--font-mono)",
										color: "var(--ink-40)",
									}}
								>
									{d.chunks > 0 ? d.chunks.toLocaleString() : "—"}
								</td>
								<td
									style={{
										padding: "11px 12px",
										fontSize: "0.7rem",
										fontFamily: "var(--font-mono)",
										color: "var(--ink-40)",
									}}
								>
									{d.date}
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);
}
