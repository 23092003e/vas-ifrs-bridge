import { FeatureUnavailable } from "@/components/FeatureUnavailable";

export default function GlUploadPage() {
	return (
		<FeatureUnavailable
			title="Upload Trial Balance"
			description="Backend GL upload và xử lý trạng thái chưa được triển khai. Bạn vẫn có thể nạp tài liệu kế toán vào Knowledge Base để tra cứu trong Chat."
			actionHref="/documents"
			actionLabel="Mở Documents"
		/>
	);
}
