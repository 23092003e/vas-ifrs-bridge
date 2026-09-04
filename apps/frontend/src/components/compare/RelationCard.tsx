"use client";

import type { RelationItem } from "@/types/compare";

interface RelationCardProps {
	relation: RelationItem | null;
	vasCode: string;
	ifrsCode: string;
}

export function RelationCard({
	relation,
	vasCode,
	ifrsCode,
}: RelationCardProps) {
	if (!relation) return null;

	const isMissingVas = relation.relationship === "missing_standard";

	return (
		<div
			style={{
				background: isMissingVas
					? "color-mix(in srgb, var(--warn) 8%, var(--surface))"
					: "color-mix(in srgb, var(--accent) 6%, var(--surface))",
				border: `1px solid ${
					isMissingVas
						? "color-mix(in srgb, var(--warn) 30%, transparent)"
						: "color-mix(in srgb, var(--accent) 30%, transparent)"
				}`,
				borderRadius: 8,
				padding: "16px 20px",
				marginBottom: 24,
			}}
		>
			<div
				style={{
					display: "flex",
					alignItems: "center",
					justifyContent: "space-between",
					marginBottom: 8,
				}}
			>
				<div style={{ display: "flex", alignItems: "center", gap: 10 }}>
					<span
						style={{
							fontSize: "0.85rem",
							fontWeight: 700,
							fontFamily: "var(--font-sans)",
							color: "var(--ink)",
						}}
					>
						{relation.topic}
					</span>
					<span
						style={{
							fontSize: "0.68rem",
							fontFamily: "var(--font-mono)",
							fontWeight: 700,
							padding: "2px 8px",
							borderRadius: 4,
							background: isMissingVas ? "var(--warn)" : "var(--accent)",
							color: isMissingVas ? "#000" : "#fff",
							textTransform: "uppercase",
						}}
					>
						{isMissingVas ? "Chưa có chuẩn mực VAS" : "Chuẩn mực tương đương"}
					</span>
				</div>

				<div
					style={{
						fontSize: "0.72rem",
						fontFamily: "var(--font-mono)",
						color: "var(--muted)",
					}}
				>
					{vasCode} ⇄ {ifrsCode}
					{relation.ias &&
						relation.ias !== ifrsCode &&
						` (tiền thân: ${relation.ias})`}
				</div>
			</div>

			<p
				style={{
					margin: 0,
					fontSize: "0.82rem",
					lineHeight: 1.6,
					color: "var(--ink-2)",
				}}
			>
				<strong style={{ color: "var(--ink)" }}>Tóm tắt cốt lõi: </strong>
				{relation.major_differences}
			</p>
		</div>
	);
}
