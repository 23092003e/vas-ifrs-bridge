"use client";

export interface PresetTopic {
	id: string;
	label: string;
	vas: string;
	ifrs: string;
	focusHint: string;
}

export const PRESET_TOPICS: PresetTopic[] = [
	{
		id: "revenue",
		label: "Doanh thu hợp đồng",
		vas: "VAS-14",
		ifrs: "IFRS-15",
		focusHint:
			"Mô hình 5 bước ghi nhận doanh thu, điều kiện chuyển giao quyền kiểm soát và nghĩa vụ thực hiện (PO).",
	},
	{
		id: "leases",
		label: "Thuê tài sản (Leases)",
		vas: "VAS-06",
		ifrs: "IFRS-16",
		focusHint:
			"Xóa bỏ phân loại thuê hoạt động ở bên thuê, ghi nhận Quyền sử dụng tài sản (ROU Asset) và Nợ thuê.",
	},
	{
		id: "ppe",
		label: "TSCĐ & Đánh giá lại",
		vas: "VAS-03",
		ifrs: "IAS-16",
		focusHint:
			"Mô hình đánh giá lại theo giá trị hợp lý (Revaluation Model) so với mô hình giá gốc (Cost Model) của VAS.",
	},
	{
		id: "inventory",
		label: "Hàng tồn kho & LIFO",
		vas: "VAS-02",
		ifrs: "IAS-2",
		focusHint:
			"Cấm phương pháp LIFO dưới IAS 2, phương pháp định giá tồn kho và điều kiện hoàn nhập giảm giá.",
	},
	{
		id: "consolidation",
		label: "Hợp nhất Báo cáo tài chính",
		vas: "VAS-25",
		ifrs: "IFRS-10",
		focusHint:
			"Quyền kiểm soát bản chất (de facto control) so với quy tắc sở hữu trên 50% quyền biểu quyết của VAS.",
	},
	{
		id: "impairment",
		label: "Tổn thất tài sản (Impairment)",
		vas: "None",
		ifrs: "IAS-36",
		focusHint:
			"Xác định giá trị có thể thu hồi (Recoverable Amount), kiểm tra tổn thất hàng năm cho Lợi thế thương mại.",
	},
	{
		id: "instruments",
		label: "Công cụ tài chính & ECL",
		vas: "None",
		ifrs: "IFRS-9",
		focusHint:
			"Mô hình tổn thất tín dụng dự kiến (ECL) thay thế mô hình tổn thất đã phát sinh, phân loại FVTPL/FVOCI.",
	},
];

interface TopicPresetsProps {
	selectedVas: string;
	selectedIfrs: string;
	onSelectPreset: (preset: PresetTopic) => void;
}

export function TopicPresets({
	selectedVas,
	selectedIfrs,
	onSelectPreset,
}: TopicPresetsProps) {
	return (
		<div style={{ marginBottom: 24 }}>
			<div
				style={{
					display: "flex",
					alignItems: "center",
					gap: 8,
					marginBottom: 10,
				}}
			>
				<span
					style={{
						fontSize: "0.72rem",
						fontFamily: "var(--font-mono)",
						fontWeight: 700,
						color: "var(--muted)",
						letterSpacing: "0.06em",
						textTransform: "uppercase",
					}}
				>
					Chủ đề đối chiếu trọng yếu
				</span>
				<span
					style={{
						fontSize: "0.72rem",
						fontFamily: "var(--font-mono)",
						color: "var(--faint)",
					}}
				>
					(Nhấn để chọn nhanh cặp chuẩn mực)
				</span>
			</div>
			<div
				style={{
					display: "flex",
					flexWrap: "wrap",
					gap: 8,
				}}
			>
				{PRESET_TOPICS.map((topic) => {
					const isActive =
						selectedVas === topic.vas && selectedIfrs === topic.ifrs;
					return (
						<button
							key={topic.id}
							type="button"
							onClick={() => onSelectPreset(topic)}
							style={{
								padding: "6px 12px",
								borderRadius: 6,
								border: isActive
									? "1.5px solid var(--accent)"
									: "1px solid var(--border)",
								background: isActive ? "var(--accent-soft)" : "var(--surface)",
								color: isActive ? "var(--accent-ink)" : "var(--ink)",
								fontSize: "0.78rem",
								fontWeight: isActive ? 600 : 500,
								cursor: "pointer",
								display: "inline-flex",
								alignItems: "center",
								gap: 6,
								transition: "all 0.15s ease",
								boxShadow: isActive ? "0 0 0 1px var(--accent)" : "none",
							}}
						>
							<span>{topic.label}</span>
							<span
								style={{
									fontSize: "0.68rem",
									fontFamily: "var(--font-mono)",
									padding: "1px 4px",
									borderRadius: 4,
									background: isActive ? "var(--accent)" : "var(--surface-2)",
									color: isActive ? "#ffffff" : "var(--muted)",
								}}
							>
								{topic.vas} ↔ {topic.ifrs}
							</span>
						</button>
					);
				})}
			</div>
		</div>
	);
}
