import { FeatureUnavailable } from "@/components/FeatureUnavailable";

export default function ComparePage() {
	return (
		<FeatureUnavailable
			title="So sánh VAS và IFRS"
			description="Trang so sánh chuyên biệt chưa có API dữ liệu chuẩn mực. Hiện tại bạn có thể yêu cầu Chat so sánh và nhận câu trả lời kèm trích dẫn nguồn."
			actionLabel="So sánh trong Chat"
		/>
	);
}
