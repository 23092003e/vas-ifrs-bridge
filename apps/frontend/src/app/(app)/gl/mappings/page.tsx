import { PipelineSandbox } from "@/components/gl/PipelineSandbox";

export default function GlMappingsPage() {
	return (
		<PipelineSandbox
			initialStep="mappings"
			title="Ma Trận Ánh Xạ Danh Mục Tài Khoản (Semantic Account Mapping)"
			description="Ánh xạ ngữ nghĩa tự động giữa hệ thống tài khoản kế toán Việt Nam (TK 111 - 911) và các khoản mục Báo cáo tài chính IFRS tương đương với chỉ số tin cậy và giải trình cơ sở chuẩn mực."
		/>
	);
}
