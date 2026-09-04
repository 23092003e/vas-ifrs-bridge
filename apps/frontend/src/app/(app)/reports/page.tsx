import { PipelineSandbox } from "@/components/gl/PipelineSandbox";

export default function ReportsPage() {
	return (
		<PipelineSandbox
			initialStep="reports"
			title="Bộ Báo Cáo Tài Chính & Thuyết Minh Chuẩn IFRS (Financial Statements & Disclosures)"
			description="Tổng hợp Báo cáo Tình hình Tài chính (Statement of Financial Position), Báo cáo Lãi Lỗ (P&L & OCI) và Bộ Thuyết minh theo chuẩn mực kế toán quốc tế, sẵn sàng cho đơn vị kiểm toán độc lập."
		/>
	);
}
