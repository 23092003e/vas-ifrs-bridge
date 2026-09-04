"use client";

import Link from "next/link";
import { useState } from "react";

export type PipelineStep = "upload" | "mappings" | "adjustments" | "reports";

interface PipelineSandboxProps {
	initialStep?: PipelineStep;
	title: string;
	description: string;
}

const STEPS: { id: PipelineStep; num: string; label: string; sub: string }[] = [
	{
		id: "upload",
		num: "01",
		label: "Trial Balance VAS",
		sub: "Nạp bảng cân đối phát sinh TT 200",
	},
	{
		id: "mappings",
		num: "02",
		label: "Account Mapping",
		sub: "Ánh xạ tài khoản tự động bằng AI",
	},
	{
		id: "adjustments",
		num: "03",
		label: "IFRS Adjustments",
		sub: "Đề xuất bút toán điều chỉnh & ROU/ECL",
	},
	{
		id: "reports",
		num: "04",
		label: "Financial Statements",
		sub: "Báo cáo IFRS & Thuyết minh tài chính",
	},
];

const SAMPLE_TB_ROWS = [
	{
		code: "1111",
		name: "Tiền mặt Việt Nam đồng",
		openDr: "1,250,000,000",
		openCr: "0",
		movDr: "8,450,000,000",
		movCr: "8,100,000,000",
		closeDr: "1,600,000,000",
		closeCr: "0",
	},
	{
		code: "1121",
		name: "Tiền gửi Ngân hàng thương mại",
		openDr: "14,820,000,000",
		openCr: "0",
		movDr: "42,100,000,000",
		movCr: "39,500,000,000",
		closeDr: "17,420,000,000",
		closeCr: "0",
	},
	{
		code: "131",
		name: "Phải thu của khách hàng",
		openDr: "32,450,000,000",
		openCr: "0",
		movDr: "68,200,000,000",
		movCr: "64,150,000,000",
		closeDr: "36,500,000,000",
		closeCr: "0",
	},
	{
		code: "1561",
		name: "Giá mua hàng hóa",
		openDr: "18,900,000,000",
		openCr: "0",
		movDr: "54,200,000,000",
		movCr: "51,800,000,000",
		closeDr: "21,300,000,000",
		closeCr: "0",
	},
	{
		code: "2111",
		name: "Nhà cửa, vật kiến trúc",
		openDr: "58,000,000,000",
		openCr: "0",
		movDr: "0",
		movCr: "0",
		closeDr: "58,000,000,000",
		closeCr: "0",
	},
	{
		code: "2141",
		name: "Hao mòn TSCĐ hữu hình",
		openDr: "0",
		openCr: "16,400,000,000",
		movDr: "0",
		movCr: "2,900,000,000",
		closeDr: "0",
		closeCr: "19,300,000,000",
	},
	{
		code: "2293",
		name: "Dự phòng phải thu khó đòi",
		openDr: "0",
		openCr: "850,000,000",
		movDr: "150,000,000",
		movCr: "300,000,000",
		closeDr: "0",
		closeCr: "1,000,000,000",
	},
	{
		code: "3411",
		name: "Vay và nợ thuê tài chính",
		openDr: "0",
		openCr: "22,000,000,000",
		movDr: "5,000,000,000",
		movCr: "8,000,000,000",
		closeDr: "0",
		closeCr: "25,000,000,000",
	},
];

const SAMPLE_MAPPINGS = [
	{
		vasCode: "131",
		vasName: "Phải thu khách hàng",
		ifrsAccount: "Trade and Other Receivables",
		standard: "IFRS 15 / IFRS 9",
		confidence: "99%",
		status: "AUTO_MAPPED",
		rule: "Tách nghĩa vụ thực hiện theo hợp đồng và đánh giá trích lập ECL",
	},
	{
		vasCode: "156",
		vasName: "Hàng hóa tồn kho",
		ifrsAccount: "Inventories (at NRV)",
		standard: "IAS 2",
		confidence: "98%",
		status: "AUTO_MAPPED",
		rule: "Đo lường theo giá thấp hơn giữa giá gốc và giá trị thuần có thể thực hiện (NRV)",
	},
	{
		vasCode: "211",
		vasName: "TSCĐ hữu hình",
		ifrsAccount: "Property, Plant & Equipment",
		standard: "IAS 16",
		confidence: "96%",
		status: "VERIFIED",
		rule: "Mô hình giá gốc (Cost Model) hoặc mô hình đánh giá lại (Revaluation Model)",
	},
	{
		vasCode: "341",
		vasName: "Nợ thuê tài chính",
		ifrsAccount: "Lease Liabilities (Current & Non-Current)",
		standard: "IFRS 16",
		confidence: "91%",
		status: "REVIEW_REQUIRED",
		rule: "Tách hợp đồng thuê hoạt động văn phòng 5 năm đưa vào bảng cân đối",
	},
];

const SAMPLE_ADJUSTMENTS = [
	{
		code: "#ADJ-01",
		title: "Ghi nhận Quyền sử dụng tài sản (ROU Asset) và Nợ thuê tài sản",
		standard: "IFRS 16 §22",
		dr: "Nợ: Right-of-Use Assets (ROU)",
		cr: "Có: Lease Liabilities (Nợ thuê tài chính)",
		amount: "12,450,000,000 VND",
		impact:
			"Tăng Tổng tài sản và Nợ phải trả; loại trừ chi phí thuê hoạt động để chuyển sang Khấu hao & Chi phí lãi vay.",
	},
	{
		code: "#ADJ-02",
		title:
			"Trích lập dự phòng tổn thất tín dụng dự kiến theo mô hình 3 giai đoạn",
		standard: "IFRS 9 §5.5",
		dr: "Nợ: ECL Impairment Loss (Chi phí P&L)",
		cr: "Có: Loss Allowance (Giảm trừ Trade Receivables)",
		amount: "420,000,000 VND",
		impact:
			"Chuyển đổi từ trích lập tổn thất đã phát sinh (TT 48) sang tổn thất tín dụng dự kiến theo ma trận dự phòng.",
	},
	{
		code: "#ADJ-03",
		title: "Ghi nhận Tài sản Thuế thu nhập hoãn lại do chênh lệch tạm thời",
		standard: "IAS 12 §24",
		dr: "Nợ: Deferred Tax Assets (DTA)",
		cr: "Có: Deferred Tax Benefit (Giảm chi phí thuế P&L)",
		amount: "2,490,000,000 VND",
		impact:
			"Chênh lệch tạm thời được khấu trừ phát sinh từ nghĩa vụ thuê IFRS 16 và dự phòng ECL vượt mức thuế chấp nhận.",
	},
];

export function PipelineSandbox({
	initialStep = "upload",
	title,
	description,
}: PipelineSandboxProps) {
	const [activeStep, setActiveStep] = useState<PipelineStep>(initialStep);
	const [showModal, setShowModal] = useState(false);
	const [submitted, setSubmitted] = useState(false);
	const [email, setEmail] = useState("");
	const [orgName, setOrgName] = useState("");

	const handleDownloadTemplate = () => {
		const headers =
			"Mã TK,Tên Tài Khoản,Dư Đầu Kỳ Nợ,Dư Đầu Kỳ Có,Phát Sinh Nợ,Phát Sinh Có,Dư Cuối Kỳ Nợ,Dư Cuối Kỳ Có\n";
		const rows = SAMPLE_TB_ROWS.map(
			(r) =>
				`"${r.code}","${r.name}",${r.openDr.replace(/,/g, "")},${r.openCr.replace(/,/g, "")},${r.movDr.replace(/,/g, "")},${r.movCr.replace(/,/g, "")},${r.closeDr.replace(/,/g, "")},${r.closeCr.replace(/,/g, "")}`,
		).join("\n");
		const csvContent = `\uFEFF${headers}${rows}`;
		const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
		const url = URL.createObjectURL(blob);
		const link = document.createElement("a");
		link.setAttribute("href", url);
		link.setAttribute(
			"download",
			"VAS_Trial_Balance_Sample_TT200_VAS_IFRS_Bridge.csv",
		);
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
	};

	const handleContactSubmit = (e: React.FormEvent) => {
		e.preventDefault();
		if (!email.trim()) return;
		setSubmitted(true);
	};

	return (
		<div
			style={{
				flex: 1,
				display: "flex",
				flexDirection: "column",
				overflowY: "auto",
				padding: "32px 28px 48px",
				maxWidth: 1200,
				margin: "0 auto",
				width: "100%",
			}}
		>
			{/* Header Banner */}
			<div
				style={{
					marginBottom: 28,
					paddingBottom: 20,
					borderBottom: "1px solid var(--border)",
				}}
			>
				<div
					style={{
						display: "inline-flex",
						alignItems: "center",
						gap: 6,
						padding: "3px 8px",
						borderRadius: "4px",
						background: "var(--accent-soft)",
						color: "var(--accent-ink)",
						fontSize: "0.68rem",
						fontFamily: "var(--font-mono)",
						fontWeight: 600,
						textTransform: "uppercase",
						letterSpacing: "0.06em",
						marginBottom: 10,
					}}
				>
					<span
						style={{
							width: 6,
							height: 6,
							borderRadius: "50%",
							background: "var(--accent)",
						}}
					/>
					Interactive Architecture Preview & Sandbox
				</div>
				<h1
					style={{
						margin: "0 0 8px",
						fontSize: "1.6rem",
						fontWeight: 600,
						color: "var(--ink)",
						letterSpacing: "-0.01em",
					}}
				>
					{title}
				</h1>
				<p
					style={{
						margin: 0,
						fontSize: "0.88rem",
						color: "var(--muted)",
						lineHeight: 1.6,
						maxWidth: 820,
					}}
				>
					{description}
				</p>
			</div>

			{/* Interactive Pipeline Stepper */}
			<div style={{ marginBottom: 28 }}>
				<div
					style={{
						fontSize: "0.72rem",
						fontFamily: "var(--font-mono)",
						color: "var(--muted)",
						textTransform: "uppercase",
						letterSpacing: "0.08em",
						marginBottom: 12,
					}}
				>
					Quy trình chuyển đổi 4 chặng (Click để xem mô phỏng từng giai đoạn)
				</div>

				<div
					style={{
						display: "grid",
						gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
						gap: 10,
					}}
				>
					{STEPS.map((step) => {
						const isSelected = activeStep === step.id;
						return (
							<button
								key={step.id}
								type="button"
								onClick={() => setActiveStep(step.id)}
								style={{
									textAlign: "left",
									padding: "14px 16px",
									borderRadius: "var(--radius-lg)",
									background: isSelected
										? "var(--surface)"
										: "var(--surface-2)",
									border: isSelected
										? "1px solid var(--accent)"
										: "1px solid var(--border)",
									boxShadow: isSelected
										? "0 0 0 1px var(--accent), 0 4px 12px rgba(0,0,0,0.05)"
										: "none",
									cursor: "pointer",
									transition: "all 140ms ease",
									position: "relative",
								}}
							>
								<div
									style={{
										display: "flex",
										alignItems: "center",
										justifyContent: "space-between",
										marginBottom: 6,
									}}
								>
									<span
										style={{
											fontFamily: "var(--font-mono)",
											fontSize: "0.72rem",
											fontWeight: 700,
											color: isSelected ? "var(--accent)" : "var(--muted)",
										}}
									>
										PHASE {step.num}
									</span>
									{isSelected && (
										<span
											style={{
												width: 6,
												height: 6,
												borderRadius: "50%",
												background: "var(--accent)",
											}}
										/>
									)}
								</div>
								<div
									style={{
										fontSize: "0.88rem",
										fontWeight: 600,
										color: "var(--ink)",
										marginBottom: 3,
									}}
								>
									{step.label}
								</div>
								<div
									style={{
										fontSize: "0.72rem",
										color: "var(--muted)",
										lineHeight: 1.4,
									}}
								>
									{step.sub}
								</div>
							</button>
						);
					})}
				</div>
			</div>

			{/* Main Sandbox Data Panel */}
			<div
				style={{
					background: "var(--surface)",
					border: "1px solid var(--border)",
					borderRadius: "var(--radius-xl)",
					boxShadow: "var(--shadow)",
					overflow: "hidden",
					marginBottom: 28,
				}}
			>
				{/* Sandbox Action Bar */}
				<div
					style={{
						padding: "14px 20px",
						borderBottom: "1px solid var(--border)",
						background: "var(--surface-2)",
						display: "flex",
						alignItems: "center",
						justifyContent: "space-between",
						flexWrap: "wrap",
						gap: 12,
					}}
				>
					<div style={{ display: "flex", alignItems: "center", gap: 10 }}>
						<span
							style={{
								fontFamily: "var(--font-mono)",
								fontSize: "0.74rem",
								fontWeight: 600,
								color: "var(--ink)",
							}}
						>
							SANDBOX DỮ LIỆU THỰC NGHIỆM:
						</span>
						<span
							style={{
								fontFamily: "var(--font-mono)",
								fontSize: "0.72rem",
								color: "var(--accent)",
								background: "var(--surface)",
								padding: "2px 8px",
								borderRadius: "4px",
								border: "1px solid var(--border)",
							}}
						>
							{activeStep === "upload" && "BẢNG CÂN ĐỐI PHÁT SINH TT 200"}
							{activeStep === "mappings" && "BẢNG ÁNH XẠ TÀI KHOẢN VAS ↔ IFRS"}
							{activeStep === "adjustments" &&
								"BÚT TOÁN ĐIỀU CHỈNH IFRS 16 & 9"}
							{activeStep === "reports" && "TÁC ĐỘNG BẢNG CÂN ĐỐI KẾ TOÁN IFRS"}
						</span>
					</div>

					<div style={{ display: "flex", alignItems: "center", gap: 8 }}>
						<button
							type="button"
							onClick={handleDownloadTemplate}
							style={{
								display: "inline-flex",
								alignItems: "center",
								gap: 6,
								padding: "6px 12px",
								borderRadius: "var(--radius-sm)",
								background: "var(--surface)",
								border: "1px solid var(--border)",
								color: "var(--ink)",
								fontSize: "0.75rem",
								fontFamily: "var(--font-mono)",
								fontWeight: 500,
								cursor: "pointer",
							}}
						>
							<svg
								width="13"
								height="13"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								strokeWidth="2"
								strokeLinecap="round"
								strokeLinejoin="round"
							>
								<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
								<polyline points="7 10 12 15 17 10" />
								<line x1="12" y1="15" x2="12" y2="3" />
							</svg>
							<span>Tải File Mẫu (.csv/.xlsx)</span>
						</button>

						<button
							type="button"
							onClick={() => setShowModal(true)}
							style={{
								display: "inline-flex",
								alignItems: "center",
								gap: 6,
								padding: "6px 14px",
								borderRadius: "var(--radius-sm)",
								background: "var(--accent)",
								border: "none",
								color: "#ffffff",
								fontSize: "0.75rem",
								fontFamily: "var(--font-mono)",
								fontWeight: 600,
								cursor: "pointer",
							}}
						>
							<span>Yêu cầu Cấu hình Doanh nghiệp</span>
							<span>→</span>
						</button>
					</div>
				</div>

				{/* Step Content: Upload / Trial Balance */}
				{activeStep === "upload" && (
					<div style={{ padding: 20 }}>
						<div
							style={{
								padding: "16px 20px",
								borderRadius: "var(--radius)",
								background: "var(--surface-2)",
								border: "1px dashed var(--border-strong)",
								marginBottom: 20,
								display: "flex",
								alignItems: "center",
								justifyContent: "space-between",
								gap: 16,
								flexWrap: "wrap",
							}}
						>
							<div>
								<div
									style={{
										fontSize: "0.85rem",
										fontWeight: 600,
										color: "var(--ink)",
										marginBottom: 4,
									}}
								>
									Cấu trúc nạp tệp Bảng cân đối phát sinh chuẩn hóa
								</div>
								<div
									style={{
										fontSize: "0.75rem",
										color: "var(--muted)",
										lineHeight: 1.5,
									}}
								>
									Hỗ trợ định dạng .xlsx, .csv theo mẫu quy định Thông tư
									200/2014/TT-BTC. Hệ thống tự động phát hiện số dư hai bên Nợ /
									Có và cân bằng kế toán.
								</div>
							</div>
							<button
								type="button"
								onClick={handleDownloadTemplate}
								style={{
									padding: "8px 14px",
									borderRadius: "4px",
									background: "var(--surface)",
									border: "1px solid var(--border)",
									color: "var(--accent-ink)",
									fontSize: "0.75rem",
									fontFamily: "var(--font-mono)",
									cursor: "pointer",
									fontWeight: 600,
									whiteSpace: "nowrap",
								}}
							>
								↓ Tải Template Chuẩn TT 200
							</button>
						</div>

						{/* Data Table */}
						<div style={{ overflowX: "auto" }}>
							<table
								style={{
									width: "100%",
									borderCollapse: "collapse",
									fontSize: "0.78rem",
									fontFamily: "var(--font-mono)",
								}}
							>
								<thead>
									<tr
										style={{
											borderBottom: "1px solid var(--border)",
											background: "var(--surface-2)",
											color: "var(--muted)",
											textAlign: "left",
										}}
									>
										<th style={{ padding: "8px 12px" }}>Mã TK</th>
										<th style={{ padding: "8px 12px" }}>Tên Tài Khoản</th>
										<th style={{ padding: "8px 12px", textAlign: "right" }}>
											Dư Đầu Nợ
										</th>
										<th style={{ padding: "8px 12px", textAlign: "right" }}>
											Dư Đầu Có
										</th>
										<th style={{ padding: "8px 12px", textAlign: "right" }}>
											Phát Sinh Nợ
										</th>
										<th style={{ padding: "8px 12px", textAlign: "right" }}>
											Phát Sinh Có
										</th>
										<th style={{ padding: "8px 12px", textAlign: "right" }}>
											Dư Cuối Nợ
										</th>
										<th style={{ padding: "8px 12px", textAlign: "right" }}>
											Dư Cuối Có
										</th>
									</tr>
								</thead>
								<tbody>
									{SAMPLE_TB_ROWS.map((row) => (
										<tr
											key={row.code}
											style={{
												borderBottom: "1px solid var(--border)",
												color: "var(--ink)",
											}}
										>
											<td
												style={{
													padding: "10px 12px",
													fontWeight: 600,
													color: "var(--accent-ink)",
												}}
											>
												{row.code}
											</td>
											<td
												style={{
													padding: "10px 12px",
													fontFamily: "var(--font-sans)",
												}}
											>
												{row.name}
											</td>
											<td
												style={{
													padding: "10px 12px",
													textAlign: "right",
													color:
														row.openDr !== "0" ? "var(--ink)" : "var(--faint)",
												}}
											>
												{row.openDr}
											</td>
											<td
												style={{
													padding: "10px 12px",
													textAlign: "right",
													color:
														row.openCr !== "0" ? "var(--ink)" : "var(--faint)",
												}}
											>
												{row.openCr}
											</td>
											<td style={{ padding: "10px 12px", textAlign: "right" }}>
												{row.movDr}
											</td>
											<td style={{ padding: "10px 12px", textAlign: "right" }}>
												{row.movCr}
											</td>
											<td
												style={{
													padding: "10px 12px",
													textAlign: "right",
													fontWeight: 600,
													color:
														row.closeDr !== "0" ? "var(--ink)" : "var(--faint)",
												}}
											>
												{row.closeDr}
											</td>
											<td
												style={{
													padding: "10px 12px",
													textAlign: "right",
													fontWeight: 600,
													color:
														row.closeCr !== "0" ? "var(--ink)" : "var(--faint)",
												}}
											>
												{row.closeCr}
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</div>
				)}

				{/* Step Content: Account Mappings */}
				{activeStep === "mappings" && (
					<div style={{ padding: 20 }}>
						<div
							style={{
								marginBottom: 16,
								fontSize: "0.8rem",
								color: "var(--muted)",
							}}
						>
							Mô hình Knowledge Graph tự động phân tích quan hệ giữa danh mục
							tài khoản VAS và chuẩn mực kế toán quốc tế tương ứng kèm độ tin
							cậy.
						</div>

						<div style={{ overflowX: "auto" }}>
							<table
								style={{
									width: "100%",
									borderCollapse: "collapse",
									fontSize: "0.78rem",
									fontFamily: "var(--font-mono)",
								}}
							>
								<thead>
									<tr
										style={{
											borderBottom: "1px solid var(--border)",
											background: "var(--surface-2)",
											color: "var(--muted)",
											textAlign: "left",
										}}
									>
										<th style={{ padding: "8px 12px" }}>Tài Khoản VAS</th>
										<th style={{ padding: "8px 12px" }}>Tài Khoản IFRS Đích</th>
										<th style={{ padding: "8px 12px" }}>Chuẩn Mực</th>
										<th style={{ padding: "8px 12px" }}>Độ Tin Cậy</th>
										<th style={{ padding: "8px 12px" }}>Trạng Thái</th>
										<th style={{ padding: "8px 12px" }}>
											Nguyên Tắc Chuyển Đổi
										</th>
									</tr>
								</thead>
								<tbody>
									{SAMPLE_MAPPINGS.map((m) => (
										<tr
											key={m.vasCode}
											style={{
												borderBottom: "1px solid var(--border)",
												color: "var(--ink)",
											}}
										>
											<td style={{ padding: "12px" }}>
												<span style={{ fontWeight: 600, color: "var(--ink)" }}>
													TK {m.vasCode}
												</span>
												<div
													style={{
														fontFamily: "var(--font-sans)",
														color: "var(--muted)",
														fontSize: "0.72rem",
													}}
												>
													{m.vasName}
												</div>
											</td>
											<td
												style={{
													padding: "12px",
													fontWeight: 600,
													color: "var(--accent-ink)",
												}}
											>
												{m.ifrsAccount}
											</td>
											<td style={{ padding: "12px" }}>
												<span
													style={{
														background: "var(--surface-2)",
														padding: "2px 6px",
														borderRadius: "4px",
														border: "1px solid var(--border)",
														fontSize: "0.7rem",
													}}
												>
													{m.standard}
												</span>
											</td>
											<td
												style={{
													padding: "12px",
													color: "var(--success)",
													fontWeight: 700,
												}}
											>
												{m.confidence}
											</td>
											<td style={{ padding: "12px" }}>
												<span
													style={{
														fontSize: "0.68rem",
														padding: "2px 6px",
														borderRadius: "4px",
														background:
															m.status === "AUTO_MAPPED"
																? "var(--accent-soft)"
																: m.status === "VERIFIED"
																	? "oklch(95% 0.04 165)"
																	: "oklch(95% 0.05 75)",
														color:
															m.status === "AUTO_MAPPED"
																? "var(--accent-ink)"
																: m.status === "VERIFIED"
																	? "var(--success)"
																	: "var(--warn)",
														fontWeight: 600,
													}}
												>
													{m.status}
												</span>
											</td>
											<td
												style={{
													padding: "12px",
													fontFamily: "var(--font-sans)",
													fontSize: "0.75rem",
													color: "var(--ink-2)",
													maxWidth: 280,
												}}
											>
												{m.rule}
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</div>
				)}

				{/* Step Content: Adjustments */}
				{activeStep === "adjustments" && (
					<div style={{ padding: 20 }}>
						<div
							style={{
								marginBottom: 16,
								fontSize: "0.8rem",
								color: "var(--muted)",
							}}
						>
							Đề xuất tự động các bút toán điều chỉnh (Adjusting Journal
							Entries) kèm nhật ký giải trình (Audit Trail) sẵn sàng cho đơn vị
							kiểm toán.
						</div>

						<div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
							{SAMPLE_ADJUSTMENTS.map((adj) => (
								<div
									key={adj.code}
									style={{
										padding: "14px 16px",
										borderRadius: "var(--radius)",
										background: "var(--surface-2)",
										border: "1px solid var(--border)",
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
										<div
											style={{ display: "flex", alignItems: "center", gap: 8 }}
										>
											<span
												style={{
													fontFamily: "var(--font-mono)",
													fontSize: "0.75rem",
													fontWeight: 700,
													color: "var(--accent-ink)",
												}}
											>
												{adj.code}
											</span>
											<span
												style={{
													fontSize: "0.84rem",
													fontWeight: 600,
													color: "var(--ink)",
												}}
											>
												{adj.title}
											</span>
										</div>
										<span
											style={{
												fontFamily: "var(--font-mono)",
												fontSize: "0.7rem",
												background: "var(--surface)",
												padding: "2px 8px",
												borderRadius: "4px",
												border: "1px solid var(--border)",
												color: "var(--muted)",
											}}
										>
											{adj.standard}
										</span>
									</div>

									<div
										style={{
											display: "grid",
											gridTemplateColumns:
												"repeat(auto-fit, minmax(260px, 1fr))",
											gap: 12,
											fontFamily: "var(--font-mono)",
											fontSize: "0.76rem",
											marginBottom: 8,
											background: "var(--surface)",
											padding: "10px 14px",
											borderRadius: "var(--radius-sm)",
											border: "1px solid var(--border)",
										}}
									>
										<div>
											<div style={{ color: "var(--accent)", fontWeight: 600 }}>
												{adj.dr}
											</div>
											<div style={{ color: "var(--ink-2)", marginTop: 4 }}>
												{adj.cr}
											</div>
										</div>
										<div
											style={{
												display: "flex",
												flexDirection: "column",
												justifyContent: "center",
												alignItems: "flex-end",
											}}
										>
											<div
												style={{ color: "var(--muted)", fontSize: "0.7rem" }}
											>
												Giá trị điều chỉnh
											</div>
											<div
												style={{
													fontSize: "0.9rem",
													fontWeight: 700,
													color: "var(--ink)",
												}}
											>
												{adj.amount}
											</div>
										</div>
									</div>

									<div
										style={{
											fontSize: "0.74rem",
											color: "var(--muted)",
											lineHeight: 1.45,
										}}
									>
										<strong style={{ color: "var(--ink-2)" }}>
											Tác động kiểm toán:
										</strong>{" "}
										{adj.impact}
									</div>
								</div>
							))}
						</div>
					</div>
				)}

				{/* Step Content: Reports */}
				{activeStep === "reports" && (
					<div style={{ padding: 20 }}>
						<div
							style={{
								marginBottom: 16,
								fontSize: "0.8rem",
								color: "var(--muted)",
							}}
						>
							Đối chiếu tổng hợp Báo cáo Tình hình Tài chính (Statement of
							Financial Position) trước và sau chuyển đổi.
						</div>

						<div
							style={{
								display: "grid",
								gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
								gap: 12,
								marginBottom: 20,
							}}
						>
							<div
								style={{
									padding: 16,
									borderRadius: "var(--radius)",
									background: "var(--surface-2)",
									border: "1px solid var(--border)",
								}}
							>
								<div
									style={{
										fontSize: "0.7rem",
										fontFamily: "var(--font-mono)",
										color: "var(--muted)",
										textTransform: "uppercase",
									}}
								>
									Tổng Tài Sản (Total Assets)
								</div>
								<div
									style={{
										fontSize: "1.4rem",
										fontWeight: 700,
										color: "var(--ink)",
										margin: "6px 0 4px",
									}}
								>
									120.20 tỷ VND
								</div>
								<div
									style={{
										fontSize: "0.74rem",
										color: "var(--success)",
										fontFamily: "var(--font-mono)",
									}}
								>
									+11.1% so với VAS (108.17 tỷ) do ROU
								</div>
							</div>

							<div
								style={{
									padding: 16,
									borderRadius: "var(--radius)",
									background: "var(--surface-2)",
									border: "1px solid var(--border)",
								}}
							>
								<div
									style={{
										fontSize: "0.7rem",
										fontFamily: "var(--font-mono)",
										color: "var(--muted)",
										textTransform: "uppercase",
									}}
								>
									Nợ Phải Trả (Total Liabilities)
								</div>
								<div
									style={{
										fontSize: "1.4rem",
										fontWeight: 700,
										color: "var(--ink)",
										margin: "6px 0 4px",
									}}
								>
									54.95 tỷ VND
								</div>
								<div
									style={{
										fontSize: "0.74rem",
										color: "var(--accent-ink)",
										fontFamily: "var(--font-mono)",
									}}
								>
									+29.3% do vốn hóa Nợ thuê tài chính
								</div>
							</div>

							<div
								style={{
									padding: 16,
									borderRadius: "var(--radius)",
									background: "var(--surface-2)",
									border: "1px solid var(--border)",
								}}
							>
								<div
									style={{
										fontSize: "0.7rem",
										fontFamily: "var(--font-mono)",
										color: "var(--muted)",
										textTransform: "uppercase",
									}}
								>
									Tác động EBITDA
								</div>
								<div
									style={{
										fontSize: "1.4rem",
										fontWeight: 700,
										color: "var(--ink)",
										margin: "6px 0 4px",
									}}
								>
									+2.80 tỷ VND
								</div>
								<div
									style={{
										fontSize: "0.74rem",
										color: "var(--success)",
										fontFamily: "var(--font-mono)",
									}}
								>
									Chuyển chi phí thuê sang Khấu hao
								</div>
							</div>
						</div>

						<div
							style={{
								padding: 16,
								borderRadius: "var(--radius)",
								background: "var(--surface-2)",
								border: "1px solid var(--border)",
								display: "flex",
								alignItems: "center",
								justifyContent: "space-between",
								flexWrap: "wrap",
								gap: 12,
							}}
						>
							<div>
								<div
									style={{
										fontSize: "0.85rem",
										fontWeight: 600,
										color: "var(--ink)",
									}}
								>
									Xuất bộ Thuyết minh Tài chính IFRS hoàn chỉnh (Notes to FS)
								</div>
								<div
									style={{
										fontSize: "0.74rem",
										color: "var(--muted)",
										marginTop: 2,
									}}
								>
									Kèm theo bảng thuyết minh phương pháp khấu hao ROU, ma trận
									ECL và tính toán thuế hoãn lại.
								</div>
							</div>
							<button
								type="button"
								onClick={() => setShowModal(true)}
								style={{
									padding: "8px 14px",
									borderRadius: "4px",
									background: "var(--ink)",
									color: "var(--surface)",
									border: "none",
									fontSize: "0.75rem",
									fontFamily: "var(--font-mono)",
									cursor: "pointer",
								}}
							>
								Đăng ký Export IFRS Report
							</button>
						</div>
					</div>
				)}
			</div>

			{/* Footnote & Alternate Action */}
			<div
				style={{
					display: "flex",
					alignItems: "center",
					justifyContent: "space-between",
					flexWrap: "wrap",
					gap: 16,
					padding: "16px 20px",
					borderRadius: "var(--radius)",
					background: "var(--surface-2)",
					border: "1px solid var(--border)",
				}}
			>
				<div>
					<div
						style={{
							fontSize: "0.84rem",
							fontWeight: 600,
							color: "var(--ink)",
						}}
					>
						Cần đối chiếu chuẩn mực và giải đáp tình huống kế toán ngay bây giờ?
					</div>
					<div
						style={{
							fontSize: "0.75rem",
							color: "var(--muted)",
							marginTop: 2,
						}}
					>
						Trợ lý AI Nova và công cụ Compare chuyên biệt đã sẵn sàng 100% tài
						liệu VAS 01-30 và IFRS 1-17.
					</div>
				</div>
				<div style={{ display: "flex", gap: 8 }}>
					<Link
						href="/compare"
						style={{
							padding: "7px 12px",
							borderRadius: "4px",
							background: "var(--surface)",
							border: "1px solid var(--border)",
							fontSize: "0.75rem",
							fontFamily: "var(--font-mono)",
							color: "var(--ink)",
							textDecoration: "none",
						}}
					>
						Mở Compare Matrix
					</Link>
					<Link
						href="/chat"
						style={{
							padding: "7px 14px",
							borderRadius: "4px",
							background: "var(--accent)",
							color: "#fff",
							fontSize: "0.75rem",
							fontFamily: "var(--font-mono)",
							fontWeight: 600,
							textDecoration: "none",
						}}
					>
						Hỏi Trợ lý Chat →
					</Link>
				</div>
			</div>

			{/* Modal: Request Enterprise Configuration */}
			{showModal && (
				<div
					style={{
						position: "fixed",
						inset: 0,
						backgroundColor: "rgba(0, 0, 0, 0.5)",
						backdropFilter: "blur(4px)",
						display: "flex",
						alignItems: "center",
						justifyContent: "center",
						zIndex: 9999,
						padding: 16,
					}}
					onClick={() => setShowModal(false)}
				>
					<div
						style={{
							backgroundColor: "var(--surface)",
							border: "1px solid var(--border)",
							borderRadius: "var(--radius-xl)",
							padding: "24px 28px",
							maxWidth: 480,
							width: "100%",
							boxShadow: "var(--shadow-lg)",
						}}
						onClick={(e) => e.stopPropagation()}
					>
						{submitted ? (
							<div style={{ textAlign: "center", padding: "16px 8px" }}>
								<div
									style={{
										width: 44,
										height: 44,
										borderRadius: "50%",
										background: "var(--accent-soft)",
										color: "var(--accent)",
										display: "flex",
										alignItems: "center",
										justifyContent: "center",
										margin: "0 auto 16px",
										fontSize: "1.2rem",
									}}
								>
									✓
								</div>
								<h3
									style={{
										margin: "0 0 8px",
										fontSize: "1.2rem",
										color: "var(--ink)",
									}}
								>
									Yêu cầu đã được ghi nhận
								</h3>
								<p
									style={{
										margin: "0 0 20px",
										fontSize: "0.82rem",
										color: "var(--muted)",
										lineHeight: 1.5,
									}}
								>
									Đội ngũ kỹ sư tài chính của VAS-IFRS Bridge sẽ liên hệ tới{" "}
									<strong style={{ color: "var(--ink)" }}>{email}</strong> để hỗ
									trợ cấu hình tích hợp dữ liệu riêng cho{" "}
									{orgName || "doanh nghiệp"}.
								</p>
								<button
									type="button"
									onClick={() => {
										setShowModal(false);
										setSubmitted(false);
									}}
									style={{
										padding: "8px 18px",
										borderRadius: "4px",
										background: "var(--accent)",
										color: "#fff",
										border: "none",
										fontSize: "0.78rem",
										fontFamily: "var(--font-mono)",
										cursor: "pointer",
									}}
								>
									Đóng thông báo
								</button>
							</div>
						) : (
							<form onSubmit={handleContactSubmit}>
								<div
									style={{
										display: "flex",
										alignItems: "center",
										justifyContent: "space-between",
										marginBottom: 16,
									}}
								>
									<h3
										style={{
											margin: 0,
											fontSize: "1.15rem",
											fontWeight: 600,
											color: "var(--ink)",
										}}
									>
										Cấu hình Doanh nghiệp & Early Access
									</h3>
									<button
										type="button"
										onClick={() => setShowModal(false)}
										style={{
											background: "none",
											border: "none",
											color: "var(--muted)",
											cursor: "pointer",
											fontSize: "1.1rem",
										}}
									>
										✕
									</button>
								</div>

								<p
									style={{
										margin: "0 0 18px",
										fontSize: "0.8rem",
										color: "var(--muted)",
										lineHeight: 1.5,
									}}
								>
									Đăng ký thử nghiệm kết nối hệ thống ERP (SAP, Oracle, Bravo,
									MISA) hoặc yêu cầu bộ quy tắc mapping IFRS tùy biến riêng.
								</p>

								<div
									style={{
										display: "flex",
										flexDirection: "column",
										gap: 12,
										marginBottom: 20,
									}}
								>
									<div>
										<label
											style={{
												display: "block",
												fontSize: "0.72rem",
												fontFamily: "var(--font-mono)",
												color: "var(--ink-2)",
												marginBottom: 4,
											}}
										>
											EMAIL DOANH NGHIỆP *
										</label>
										<input
											type="email"
											required
											value={email}
											onChange={(e) => setEmail(e.target.value)}
											placeholder="cfo@tapdoan.vn"
											style={{
												width: "100%",
												padding: "8px 12px",
												borderRadius: "4px",
												border: "1px solid var(--border)",
												background: "var(--surface-2)",
												color: "var(--ink)",
												fontSize: "0.82rem",
												outline: "none",
											}}
										/>
									</div>

									<div>
										<label
											style={{
												display: "block",
												fontSize: "0.72rem",
												fontFamily: "var(--font-mono)",
												color: "var(--ink-2)",
												marginBottom: 4,
											}}
										>
											TÊN TẬP ĐOÀN / DOANH NGHIỆP
										</label>
										<input
											type="text"
											value={orgName}
											onChange={(e) => setOrgName(e.target.value)}
											placeholder="Tập đoàn FDI / Niêm yết..."
											style={{
												width: "100%",
												padding: "8px 12px",
												borderRadius: "4px",
												border: "1px solid var(--border)",
												background: "var(--surface-2)",
												color: "var(--ink)",
												fontSize: "0.82rem",
												outline: "none",
											}}
										/>
									</div>
								</div>

								<div
									style={{
										display: "flex",
										justifyContent: "flex-end",
										gap: 10,
									}}
								>
									<button
										type="button"
										onClick={() => setShowModal(false)}
										style={{
											padding: "7px 14px",
											borderRadius: "4px",
											border: "1px solid var(--border)",
											background: "transparent",
											color: "var(--muted)",
											fontSize: "0.75rem",
											fontFamily: "var(--font-mono)",
											cursor: "pointer",
										}}
									>
										Hủy
									</button>
									<button
										type="submit"
										style={{
											padding: "7px 16px",
											borderRadius: "4px",
											border: "none",
											background: "var(--accent)",
											color: "#fff",
											fontSize: "0.75rem",
											fontFamily: "var(--font-mono)",
											fontWeight: 600,
											cursor: "pointer",
										}}
									>
										Gửi yêu cầu cấu hình
									</button>
								</div>
							</form>
						)}
					</div>
				</div>
			)}
		</div>
	);
}
