import Link from "next/link";

interface FeatureUnavailableProps {
	title: string;
	description: string;
	actionHref?: string;
	actionLabel?: string;
}

export function FeatureUnavailable({
	title,
	description,
	actionHref = "/chat",
	actionLabel = "Mở Chat",
}: FeatureUnavailableProps) {
	return (
		<main
			style={{
				flex: 1,
				display: "grid",
				placeItems: "center",
				padding: 32,
				background: "var(--chat-bg)",
			}}
		>
			<section
				style={{
					width: "100%",
					maxWidth: 560,
					padding: 32,
					border: "1px solid var(--rule)",
					borderRadius: 8,
					background: "var(--surface)",
				}}
			>
				<div
					style={{
						width: 32,
						height: 2,
						marginBottom: 16,
						background: "var(--accent)",
					}}
				/>
				<p
					style={{
						margin: "0 0 8px",
						font: "600 0.68rem var(--font-mono)",
						letterSpacing: "0.08em",
						textTransform: "uppercase",
						color: "var(--accent)",
					}}
				>
					Đang phát triển
				</p>
				<h1
					style={{
						margin: "0 0 12px",
						fontFamily: "var(--font-lora, Georgia, serif)",
						fontSize: "1.5rem",
						color: "var(--ink)",
					}}
				>
					{title}
				</h1>
				<p
					style={{
						margin: "0 0 24px",
						lineHeight: 1.65,
						fontSize: "0.85rem",
						color: "var(--ink-60)",
					}}
				>
					{description}
				</p>
				<Link
					href={actionHref}
					style={{
						display: "inline-flex",
						padding: "9px 14px",
						borderRadius: 4,
						background: "var(--accent)",
						color: "white",
						textDecoration: "none",
						font: "600 0.75rem var(--font-mono)",
					}}
				>
					{actionLabel}
				</Link>
			</section>
		</main>
	);
}
