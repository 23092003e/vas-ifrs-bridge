"use client";

export default function GlMappingsPage() {
	const mappings = [
		{
			vas: "1111",
			vasName: "Tiền mặt tại quỹ",
			ifrs: "Cash and cash equivalents",
			category: "Current Assets",
			confidence: 0.98,
		},
		{
			vas: "1112",
			vasName: "Tiền mặt ngoại tệ",
			ifrs: "Cash and cash equivalents (FX)",
			category: "Current Assets",
			confidence: 0.96,
		},
		{
			vas: "1121",
			vasName: "Tiền gửi ngân hàng",
			ifrs: "Cash and cash equivalents",
			category: "Current Assets",
			confidence: 0.97,
		},
		{
			vas: "1311",
			vasName: "Phải thu của khách hàng",
			ifrs: "Trade receivables",
			category: "Current Assets",
			confidence: 0.99,
		},
		{
			vas: "1521",
			vasName: "Nguyên liệu, vật liệu",
			ifrs: "Inventories — Raw materials",
			category: "Current Assets",
			confidence: 0.95,
		},
		{
			vas: "2111",
			vasName: "TSCĐ hữu hình — Nguyên giá",
			ifrs: "Property, plant and equipment",
			category: "Non-current Assets",
			confidence: 0.94,
		},
		{
			vas: "3311",
			vasName: "Phải trả người bán",
			ifrs: "Trade payables",
			category: "Current Liabilities",
			confidence: 0.99,
		},
		{
			vas: "4111",
			vasName: "Vốn đầu tư của chủ sở hữu",
			ifrs: "Share capital",
			category: "Equity",
			confidence: 0.97,
		},
	];

	const confColor = (c: number) =>
		c >= 0.95
			? "var(--score-high)"
			: c >= 0.8
				? "var(--score-mid)"
				: "var(--score-low)";

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
						Account Mappings
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
						VAS account codes mapped to IFRS line items
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
					EXPORT MAPPINGS
				</button>
			</div>
			<div style={{ padding: "24px 32px" }}>
				<table style={{ width: "100%", borderCollapse: "collapse" }}>
					<thead>
						<tr style={{ borderBottom: "2px solid var(--ink)" }}>
							{[
								"VAS Code",
								"VAS Name",
								"IFRS Line Item",
								"Category",
								"Confidence",
							].map((h) => (
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
						{mappings.map((m, i) => (
							<tr
								key={i}
								style={{ borderBottom: "1px solid var(--rule)" }}
								onMouseEnter={(e) => {
									(e.currentTarget as HTMLElement).style.background =
										"var(--accent-light)";
								}}
								onMouseLeave={(e) => {
									(e.currentTarget as HTMLElement).style.background =
										"transparent";
								}}
							>
								<td style={{ padding: "10px 12px" }}>
									<span
										style={{
											fontSize: "0.78rem",
											fontFamily: "var(--font-mono)",
											fontWeight: 700,
											color: "var(--accent)",
										}}
									>
										{m.vas}
									</span>
								</td>
								<td
									style={{
										padding: "10px 12px",
										fontSize: "0.78rem",
										fontFamily: "var(--font-lora, Georgia, serif)",
										color: "var(--ink)",
									}}
								>
									{m.vasName}
								</td>
								<td
									style={{
										padding: "10px 12px",
										fontSize: "0.78rem",
										fontFamily: "var(--font-lora, Georgia, serif)",
										color: "var(--ink)",
									}}
								>
									{m.ifrs}
								</td>
								<td style={{ padding: "10px 12px" }}>
									<span
										style={{
											fontSize: "0.63rem",
											fontFamily: "var(--font-mono)",
											padding: "2px 6px",
											borderRadius: 2,
											background: "var(--paper-alt)",
											color: "var(--ink-60)",
										}}
									>
										{m.category}
									</span>
								</td>
								<td style={{ padding: "10px 12px" }}>
									<span
										style={{
											fontSize: "0.73rem",
											fontFamily: "var(--font-mono)",
											fontWeight: 700,
											color: confColor(m.confidence),
										}}
									>
										{(m.confidence * 100).toFixed(0)}%
									</span>
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);
}
