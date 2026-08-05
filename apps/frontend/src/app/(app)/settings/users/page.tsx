import { FeatureUnavailable } from "@/components/FeatureUnavailable";

export default function UsersSettingsPage() {
	return (
		<FeatureUnavailable
			title="User Management"
			description="Mời thành viên và thay đổi role cần API quản trị được bảo vệ. Danh sách người dùng mẫu đã được gỡ để không lộ dữ liệu giả như tài khoản thật."
		/>
	);
}
