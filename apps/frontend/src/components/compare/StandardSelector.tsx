"use client";

import type { StandardItem } from "@/types/compare";

interface StandardSelectorProps {
	vasList: StandardItem[];
	ifrsList: StandardItem[];
	selectedVas: string;
	selectedIfrs: string;
	focusQuery: string;
	loading: boolean;
	onVasChange: (vas: string) => void;
	onIfrsChange: (ifrs: string) => void;
	onFocusQueryChange: (query: string) => void;
	onCompare: () => void;
	onReset: () => void;
}

export function StandardSelector({
	vasList,
	ifrsList,
	selectedVas,
	selectedIfrs,
	focusQuery,
	loading,
	onVasChange,
	onIfrsChange,
	onFocusQueryChange,
	onCompare,
	onReset,
}: StandardSelectorProps) {
	const currentVas = vasList.find((v) => v.code === selectedVas);
	const currentIfrs = ifrsList.find((i) => i.code === selectedIfrs);

	return (
		<div
			style={{
				background: "var(--surface)",
				border: "1px solid var(--border)",
				borderRadius: 8,
				padding: "20px 24px",
				marginBottom: 24,
				boxShadow: "var(--shadow-sm)",
			}}
		>
			<div
				style={{
					display: "grid",
					gridTemplateColumns: "1fr auto 1fr",
					gap: 16,
					alignItems: "center",
					marginBottom: 16,
				}}
			>
				{/* VAS Selection Column */}
				<div>
					<label
						htmlFor="vas-standard-select"
						style={{
							display: "block",
							fontSize: "0.72rem",
							fontFamily: "var(--font-mono)",
							fontWeight: 700,
							color: "var(--muted)",
							textTransform: "uppercase",
							letterSpacing: "0.06em",
							marginBottom: 6,
						}}
					>
						Chuẩn mực VAS (Việt Nam)
					</label>
					<div style={{ position: "relative" }}>
						<select
							id="vas-standard-select"
							value={selectedVas}
							onChange={(e) => onVasChange(e.target.value)}
							style={{
								width: "100%",
								padding: "10px 14px",
								fontSize: "0.85rem",
								fontFamily: "var(--font-sans)",
								fontWeight: 500,
								color: "var(--ink)",
								background: "var(--surface-2)",
								border: "1px solid var(--border)",
								borderRadius: 6,
								appearance: "none",
								cursor: "pointer",
								outline: "none",
							}}
						>
							<option value="None">
								None (Chưa có chuẩn mực VAS tương đương)
							</option>
							{vasList.map((vas) => (
								<option key={vas.code} value={vas.code}>
									{vas.code}: {vas.name}
								</option>
							))}
						</select>
						<span
							style={{
								position: "absolute",
								right: 12,
								top: "50%",
								transform: "translateY(-50%)",
								pointerEvents: "none",
								color: "var(--muted)",
								fontSize: "0.75rem",
							}}
						>
							▼
						</span>
					</div>
					{currentVas && (
						<div
							style={{
								marginTop: 6,
								fontSize: "0.72rem",
								fontFamily: "var(--font-mono)",
								color: "var(--muted)",
								display: "flex",
								alignItems: "center",
								gap: 6,
							}}
						>
							<span
								style={{
									padding: "1px 6px",
									borderRadius: 4,
									background: "var(--surface-3)",
									color: "var(--ink-2)",
								}}
							>
								{currentVas.category}
							</span>
							<span
								style={{
									overflow: "hidden",
									textOverflow: "ellipsis",
									whiteSpace: "nowrap",
								}}
							>
								{currentVas.name}
							</span>
						</div>
					)}
				</div>

				{/* Connector / Direction Indicator */}
				<div
					style={{
						display: "flex",
						flexDirection: "column",
						alignItems: "center",
						justifyContent: "center",
						paddingTop: 18,
					}}
				>
					<div
						style={{
							width: 36,
							height: 36,
							borderRadius: "50%",
							background: "var(--surface-2)",
							border: "1px solid var(--border)",
							display: "flex",
							alignItems: "center",
							justifyContent: "center",
							color: "var(--accent)",
							fontWeight: 700,
							fontSize: "0.85rem",
						}}
						title="Đối chiếu hai chiều VAS và IFRS"
					>
						⇄
					</div>
				</div>

				{/* IFRS Selection Column */}
				<div>
					<label
						htmlFor="ifrs-standard-select"
						style={{
							display: "block",
							fontSize: "0.72rem",
							fontFamily: "var(--font-mono)",
							fontWeight: 700,
							color: "var(--muted)",
							textTransform: "uppercase",
							letterSpacing: "0.06em",
							marginBottom: 6,
						}}
					>
						Chuẩn mực IFRS / IAS (Quốc tế)
					</label>
					<div style={{ position: "relative" }}>
						<select
							id="ifrs-standard-select"
							value={selectedIfrs}
							onChange={(e) => onIfrsChange(e.target.value)}
							style={{
								width: "100%",
								padding: "10px 14px",
								fontSize: "0.85rem",
								fontFamily: "var(--font-sans)",
								fontWeight: 500,
								color: "var(--ink)",
								background: "var(--surface-2)",
								border: "1px solid var(--border)",
								borderRadius: 6,
								appearance: "none",
								cursor: "pointer",
								outline: "none",
							}}
						>
							<option value="None">None (Không xác định chuẩn mực IFRS)</option>
							{ifrsList.map((ifrs) => (
								<option key={ifrs.code} value={ifrs.code}>
									{ifrs.code}: {ifrs.name}
								</option>
							))}
						</select>
						<span
							style={{
								position: "absolute",
								right: 12,
								top: "50%",
								transform: "translateY(-50%)",
								pointerEvents: "none",
								color: "var(--muted)",
								fontSize: "0.75rem",
							}}
						>
							▼
						</span>
					</div>
					{currentIfrs && (
						<div
							style={{
								marginTop: 6,
								fontSize: "0.72rem",
								fontFamily: "var(--font-mono)",
								color: "var(--muted)",
								display: "flex",
								alignItems: "center",
								gap: 6,
							}}
						>
							<span
								style={{
									padding: "1px 6px",
									borderRadius: 4,
									background: "var(--surface-3)",
									color: "var(--ink-2)",
								}}
							>
								{currentIfrs.category}
							</span>
							<span
								style={{
									overflow: "hidden",
									textOverflow: "ellipsis",
									whiteSpace: "nowrap",
								}}
							>
								{currentIfrs.name}
							</span>
						</div>
					)}
				</div>
			</div>

			{/* Focus Question / Specific Aspect Input */}
			<div style={{ marginBottom: 16 }}>
				<label
					htmlFor="focus-query-input"
					style={{
						display: "block",
						fontSize: "0.72rem",
						fontFamily: "var(--font-mono)",
						fontWeight: 700,
						color: "var(--muted)",
						textTransform: "uppercase",
						letterSpacing: "0.06em",
						marginBottom: 6,
					}}
				>
					Câu hỏi hoặc khía cạnh trọng tâm (Tùy chọn)
				</label>
				<input
					id="focus-query-input"
					type="text"
					value={focusQuery}
					onChange={(e) => onFocusQueryChange(e.target.value)}
					placeholder="Ví dụ: Nguyên tắc ghi nhận ban đầu, điều kiện vốn hóa, hoặc cách hạch toán bút toán chuyển đổi..."
					style={{
						width: "100%",
						padding: "10px 14px",
						fontSize: "0.85rem",
						fontFamily: "var(--font-sans)",
						color: "var(--ink)",
						background: "var(--surface-2)",
						border: "1px solid var(--border)",
						borderRadius: 6,
						outline: "none",
						boxSizing: "border-box",
					}}
					onKeyDown={(e) => {
						if (e.key === "Enter" && !loading) {
							e.preventDefault();
							onCompare();
						}
					}}
				/>
			</div>

			{/* Action Toolbar */}
			<div
				style={{
					display: "flex",
					justifyContent: "flex-end",
					alignItems: "center",
					gap: 12,
				}}
			>
				<button
					type="button"
					onClick={onReset}
					style={{
						padding: "8px 16px",
						fontSize: "0.78rem",
						fontFamily: "var(--font-mono)",
						color: "var(--muted)",
						background: "transparent",
						border: "1px solid var(--border)",
						borderRadius: 6,
						cursor: "pointer",
					}}
				>
					{loading ? "Dừng đối chiếu" : "Đặt lại"}
				</button>
				<button
					type="button"
					onClick={onCompare}
					disabled={loading || (!selectedVas && !selectedIfrs)}
					style={{
						padding: "8px 20px",
						fontSize: "0.82rem",
						fontFamily: "var(--font-mono)",
						fontWeight: 700,
						letterSpacing: "0.04em",
						color: "#ffffff",
						background: loading ? "var(--faint)" : "var(--accent)",
						border: "none",
						borderRadius: 6,
						cursor: loading ? "wait" : "pointer",
						display: "inline-flex",
						alignItems: "center",
						gap: 8,
						boxShadow: "var(--shadow)",
					}}
				>
					{loading ? (
						<>
							<span
								style={{
									width: 12,
									height: 12,
									border: "2px solid #ffffff",
									borderTopColor: "transparent",
									borderRadius: "50%",
									display: "inline-block",
									animation: "spin 0.8s linear infinite",
								}}
							/>
							<span>ĐANG PHÂN TÍCH...</span>
						</>
					) : (
						<>
							<span>⚡</span>
							<span>SO SÁNH NGAY (AI RAG)</span>
						</>
					)}
				</button>
			</div>
		</div>
	);
}
