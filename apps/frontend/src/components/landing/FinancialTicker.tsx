"use client";

const TICKER_ITEMS = [
	{
		code: "VAS 14 ➔ IFRS 15",
		status: "SYNCED",
		change: "Mô hình 5 bước",
		up: true,
	},
	{
		code: "IFRS 16 (Thuê tài sản)",
		status: "ACTIVE",
		change: "Vốn hóa ROU Asset +11.1%",
		up: true,
	},
	{
		code: "IFRS 9 (Công cụ tài chính)",
		status: "ECL MODEL",
		change: "Stage 1-3 thay thế TT 48",
		up: true,
	},
	{
		code: "IAS 12 (Thuế TNDN)",
		status: "BS METHOD",
		change: "Tài sản thuế hoãn lại DTA",
		up: true,
	},
	{
		code: "QĐ 345/QĐ-BTC",
		status: "MANDATE",
		change: "Lộ trình IFRS Bộ Tài chính",
		up: true,
	},
	{
		code: "ONTOLOGY GRAPH",
		status: "ONLINE",
		change: "200+ Quan hệ đối chiếu",
		up: true,
	},
	{
		code: "AUDIT TRAIL",
		status: "SHA-256",
		change: "100% Sẵn sàng cho Big 4",
		up: true,
	},
	{
		code: "ZERO DATA TRAINING",
		status: "ENTERPRISE",
		change: "Bảo mật dữ liệu tuyệt đối",
		up: true,
	},
];

export function FinancialTicker() {
	return (
		<div className="financial-ticker-bar" aria-hidden="true">
			<div className="ticker-track">
				{/* Double loop for seamless infinite marquee */}
				{[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
					<div key={`${item.code}-${i}`} className="ticker-item">
						<span className="ticker-dot" />
						<span className="ticker-code">{item.code}</span>
						<span className="ticker-status">{item.status}</span>
						<span className="ticker-change">{item.change}</span>
					</div>
				))}
			</div>
		</div>
	);
}
