import { PipelineSandbox } from "@/components/gl/PipelineSandbox";

export default function GlAdjustmentsPage() {
	return (
		<PipelineSandbox
			initialStep="adjustments"
			title="Đề Xuất Bút Toán Điều Chỉnh Chuyển Đổi (IFRS Adjustments)"
			description="Tự động tính toán và tạo các bút toán tái phân loại (Reclassification) và tái đo lường (Remeasurement) theo IFRS 16 (Thuê tài sản), IFRS 9 (Tổn thất tín dụng dự kiến ECL) và IAS 12 (Thuế hoãn lại)."
		/>
	);
}
