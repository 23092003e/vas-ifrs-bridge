import { FeatureUnavailable } from "@/components/FeatureUnavailable";

export default function AuditSettingsPage() {
	return (
		<FeatureUnavailable
			title="Audit Log"
			description="API truy vấn audit log chưa được công bố cho frontend. Nhật ký mẫu đã được gỡ để không bị hiểu nhầm là sự kiện bảo mật thật."
		/>
	);
}
