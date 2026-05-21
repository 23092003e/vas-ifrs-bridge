"use client";

export default function GlAdjustmentsPage() {
	const adjustments = [
		{
			ref: "ADJ-001",
			description: "Reclassify finance lease (IAS 17 → IFRS 16)",
			account: "2111 / 3411",
			debit: 450000000,
			credit: 450000000,
			status: "Auto",
		},
		{
			ref: "ADJ-002",
			description: "Revenue recognition timing adjustment (IFRS 15)",
			account: "3311 / 5111",
			debit: 120000000,
			credit: 120000000,
			status: "Auto",
		},
		{
			ref: "ADJ-003",
			description: "Expected credit loss provision (IFRS 9)",
			account: "6426 / 1592",
			debit: 35000000,
			credit: 35000000,
			status: "Review",
		},
		{
			ref: "ADJ-004",
			description: "Deferred tax adjustment (IAS 12)",
			account: "8212 / 3434",
			debit: 18500000,
			credit: 18500000,
			status: "Auto",
		},
		{
			ref: "ADJ-005",
			description: "Share-based payment expense (IFRS 2)",
			account: "6422 / 4118",
			debit: 65000000,
			credit: 65000000,
			status: "Review",
		},
	];

	const statusColor = (s: string) =>
		s === "Auto" ? "var(--score-high)" : "var(--score-mid)";
	function fmt(n: number) {
		return new Intl.NumberFormat("vi-VN").format(n);
	}

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
						IFRS Adjustments
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
						Journal entries for VAS → IFRS transformation
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
					APPROVE ALL
				</button>
			</div>
			<div
				style={{
					padding: "12px 32px",
					borderBottom: "1px solid var(--rule)",
					background: "var(--paper-alt)",
					display: "flex",
					gap: 40,
				}}
			>
				{[
					["Total Adjustments", "5"],
					["Auto-generated", "3"],
					["Pending Review", "2"],
					["Total Debit (VND)", "688,500,000"],
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
								fontSize: "1rem",
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
							{[
								"Ref",
								"Description",
								"Accounts",
								"Debit (VND)",
								"Credit (VND)",
								"Type",
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
						{adjustments.map((a, i) => (
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
											fontSize: "0.7rem",
											fontFamily: "var(--font-mono)",
											fontWeight: 700,
											color: "var(--accent)",
										}}
									>
										{a.ref}
									</span>
								</td>
								<td
									style={{
										padding: "10px 12px",
										fontSize: "0.78rem",
										fontFamily: "var(--font-lora, Georgia, serif)",
										color: "var(--ink)",
										maxWidth: 300,
									}}
								>
									{a.description}
								</td>
								<td style={{ padding: "10px 12px" }}>
									<span
										style={{
											fontSize: "0.68rem",
											fontFamily: "var(--font-mono)",
											color: "var(--ink-60)",
										}}
									>
										{a.account}
									</span>
								</td>
								<td
									style={{
										padding: "10px 12px",
										fontSize: "0.75rem",
										fontFamily: "var(--font-mono)",
										color: "var(--ink)",
										textAlign: "right",
									}}
								>
									{fmt(a.debit)}
								</td>
								<td
									style={{
										padding: "10px 12px",
										fontSize: "0.75rem",
										fontFamily: "var(--font-mono)",
										color: "var(--ink)",
										textAlign: "right",
									}}
								>
									{fmt(a.credit)}
								</td>
								<td style={{ padding: "10px 12px" }}>
									<span
										style={{
											fontSize: "0.65rem",
											fontFamily: "var(--font-mono)",
											fontWeight: 700,
											color: statusColor(a.status),
										}}
									>
										{a.status}
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
