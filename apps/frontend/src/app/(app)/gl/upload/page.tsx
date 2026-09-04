import { PipelineSandbox } from "@/components/gl/PipelineSandbox";

export default function GlUploadPage() {
	return (
		<PipelineSandbox
			initialStep="upload"
			title="Nạp & Phân Tích Bảng Cân Đối Phát Sinh (VAS Trial Balance)"
			description="Trích xuất dữ liệu tự động từ Bảng cân đối phát sinh tài khoản kế toán theo Thông tư 200/2014/TT-BTC. Kiểm tra tính cân bằng Nợ/Có và chuẩn bị ma trận ánh xạ sang hệ thống IFRS."
		/>
	);
}
