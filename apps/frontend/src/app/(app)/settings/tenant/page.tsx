import { FeatureUnavailable } from "@/components/FeatureUnavailable";

export default function TenantSettingsPage() {
	return (
		<FeatureUnavailable
			title="Workspace Settings"
			description="Cập nhật tenant cần API quản trị và phân quyền server-side. Form cục bộ không lưu dữ liệu đã được thay bằng trạng thái rõ ràng này."
		/>
	);
}
