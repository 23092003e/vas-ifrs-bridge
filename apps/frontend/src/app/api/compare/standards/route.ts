import { authenticatedBackendFetch } from "@/lib/server/backend";
import type { StandardsData } from "@/types/compare";
import { NextResponse } from "next/server";

const FALLBACK_VAS_STANDARDS = [
	{
		code: "VAS-01",
		name: "Chuẩn mực chung (Framework)",
		category: "Presentation",
	},
	{ code: "VAS-02", name: "Hàng tồn kho (Inventories)", category: "Assets" },
	{
		code: "VAS-03",
		name: "Tài sản cố định hữu hình (PPE)",
		category: "Assets",
	},
	{
		code: "VAS-04",
		name: "Tài sản cố định vô hình (Intangible Assets)",
		category: "Assets",
	},
	{
		code: "VAS-05",
		name: "Bất động sản đầu tư (Investment Property)",
		category: "Assets",
	},
	{ code: "VAS-06", name: "Thuê tài sản (Leases)", category: "Liabilities" },
	{
		code: "VAS-07",
		name: "Kế toán các khoản đầu tư vào công ty liên kết",
		category: "Group",
	},
	{
		code: "VAS-08",
		name: "Thông tin tài chính về những khoản vốn góp liên doanh",
		category: "Group",
	},
	{
		code: "VAS-10",
		name: "Ảnh hưởng của việc thay đổi tỷ giá hối đoái",
		category: "Foreign Exchange",
	},
	{
		code: "VAS-11",
		name: "Hợp nhất kinh doanh (Business Combinations)",
		category: "Group",
	},
	{
		code: "VAS-14",
		name: "Doanh thu và thu nhập khác (Revenue)",
		category: "Income",
	},
	{
		code: "VAS-15",
		name: "Hợp đồng xây dựng (Construction Contracts)",
		category: "Income",
	},
	{
		code: "VAS-16",
		name: "Chi phí đi vay (Borrowing Costs)",
		category: "Expenses",
	},
	{
		code: "VAS-17",
		name: "Thuế thu nhập doanh nghiệp (Income Taxes)",
		category: "Taxes",
	},
	{
		code: "VAS-18",
		name: "Các khoản dự phòng, tài sản và nợ tiềm tàng",
		category: "Liabilities",
	},
	{
		code: "VAS-19",
		name: "Hợp đồng bảo hiểm (Insurance Contracts)",
		category: "Specialized",
	},
	{
		code: "VAS-21",
		name: "Trình bày báo cáo tài chính",
		category: "Presentation",
	},
	{
		code: "VAS-22",
		name: "Trình bày bổ sung BCTC của ngân hàng",
		category: "Specialized",
	},
	{
		code: "VAS-23",
		name: "Các sự kiện phát sinh sau ngày kết thúc kỳ kế toán năm",
		category: "General",
	},
	{
		code: "VAS-24",
		name: "Báo cáo lưu chuyển tiền tệ (Cash Flows)",
		category: "Presentation",
	},
	{
		code: "VAS-25",
		name: "BCTC hợp nhất và kế toán khoản đầu tư vào công ty con",
		category: "Group",
	},
	{
		code: "VAS-26",
		name: "Thông tin về các bên liên quan (Related Parties)",
		category: "Disclosure",
	},
	{
		code: "VAS-27",
		name: "Báo cáo tài chính giữa niên độ",
		category: "Presentation",
	},
	{
		code: "VAS-28",
		name: "Báo cáo bộ phận (Segment Reporting)",
		category: "Disclosure",
	},
	{
		code: "VAS-29",
		name: "Thay đổi chính sách kế toán, ước tính kế toán và sai sót",
		category: "General",
	},
	{
		code: "VAS-30",
		name: "Lãi trên cổ phiếu (Earnings per Share)",
		category: "Presentation",
	},
];

const FALLBACK_IFRS_STANDARDS = [
	{ code: "IFRS-1", name: "First-time Adoption of IFRS", category: "General" },
	{ code: "IFRS-2", name: "Share-based Payment", category: "Expenses" },
	{ code: "IFRS-3", name: "Business Combinations", category: "Group" },
	{
		code: "IFRS-5",
		name: "Non-current Assets Held for Sale and Discontinued Operations",
		category: "Assets",
	},
	{
		code: "IFRS-7",
		name: "Financial Instruments: Disclosures",
		category: "Financial Instruments",
	},
	{ code: "IFRS-8", name: "Operating Segments", category: "Disclosure" },
	{
		code: "IFRS-9",
		name: "Financial Instruments",
		category: "Financial Instruments",
	},
	{
		code: "IFRS-10",
		name: "Consolidated Financial Statements",
		category: "Group",
	},
	{ code: "IFRS-11", name: "Joint Arrangements", category: "Group" },
	{
		code: "IFRS-12",
		name: "Disclosure of Interests in Other Entities",
		category: "Disclosure",
	},
	{ code: "IFRS-13", name: "Fair Value Measurement", category: "Measurement" },
	{
		code: "IFRS-15",
		name: "Revenue from Contracts with Customers",
		category: "Income",
	},
	{ code: "IFRS-16", name: "Leases", category: "Liabilities" },
	{ code: "IFRS-17", name: "Insurance Contracts", category: "Specialized" },
	{
		code: "IAS-1",
		name: "Presentation of Financial Statements",
		category: "Presentation",
	},
	{ code: "IAS-2", name: "Inventories", category: "Assets" },
	{ code: "IAS-7", name: "Statement of Cash Flows", category: "Presentation" },
	{
		code: "IAS-8",
		name: "Accounting Policies, Changes in Accounting Estimates and Errors",
		category: "General",
	},
	{ code: "IAS-12", name: "Income Taxes", category: "Taxes" },
	{ code: "IAS-16", name: "Property, Plant and Equipment", category: "Assets" },
	{ code: "IAS-19", name: "Employee Benefits", category: "Expenses" },
	{
		code: "IAS-20",
		name: "Accounting for Government Grants",
		category: "Income",
	},
	{
		code: "IAS-21",
		name: "The Effects of Changes in Foreign Exchange Rates",
		category: "Foreign Exchange",
	},
	{ code: "IAS-23", name: "Borrowing Costs", category: "Expenses" },
	{ code: "IAS-24", name: "Related Party Disclosures", category: "Disclosure" },
	{ code: "IAS-27", name: "Separate Financial Statements", category: "Group" },
	{
		code: "IAS-28",
		name: "Investments in Associates and Joint Ventures",
		category: "Group",
	},
	{
		code: "IAS-32",
		name: "Financial Instruments: Presentation",
		category: "Financial Instruments",
	},
	{ code: "IAS-36", name: "Impairment of Assets", category: "Assets" },
	{
		code: "IAS-37",
		name: "Provisions, Contingent Liabilities and Contingent Assets",
		category: "Liabilities",
	},
	{ code: "IAS-38", name: "Intangible Assets", category: "Assets" },
	{ code: "IAS-40", name: "Investment Property", category: "Assets" },
];

const FALLBACK_RELATIONS = [
	{
		topic: "Revenue Recognition",
		vas: "VAS-14",
		ifrs: "IFRS-15",
		ias: "IAS-18",
		relationship: "equivalent_standard",
		major_differences:
			"VAS 14 áp dụng mô hình 5 điều kiện bán hàng hóa và 4 điều kiện cung cấp dịch vụ (chuyển giao rủi ro & lợi ích). IFRS 15 đưa ra mô hình thống nhất 5 bước dựa trên chuyển giao quyền kiểm soát (control), phân bổ giá giao dịch theo SSP và ghi nhận nghĩa vụ thực hiện riêng biệt.",
	},
	{
		topic: "Leases",
		vas: "VAS-06",
		ifrs: "IFRS-16",
		ias: "IAS-17",
		relationship: "equivalent_standard",
		major_differences:
			"VAS 06 phân loại thuê hoạt động và thuê tài chính cho cả bên thuê lẫn bên cho thuê (thuê hoạt động không ghi nhận trên BCTC). IFRS 16 loại bỏ mô hình thuê hoạt động đối với bên thuê, bắt buộc ghi nhận Quyền sử dụng tài sản (ROU Asset) và Nợ phải trả thuê tài sản (Lease Liability) trên Bảng CĐKT.",
	},
	{
		topic: "Property Plant Equipment",
		vas: "VAS-03",
		ifrs: "IAS-16",
		ias: "IAS-16",
		relationship: "equivalent_standard",
		major_differences:
			"VAS 03 chỉ cho phép mô hình giá gốc (Cost Model), khấu hao theo quy định thuế/khung của Bộ Tài chính. IAS 16 cho phép lựa chọn giữa Cost Model và Revaluation Model (đánh giá lại theo giá trị hợp lý qua OCI).",
	},
	{
		topic: "Inventory",
		vas: "VAS-02",
		ifrs: "IAS-2",
		ias: "IAS-2",
		relationship: "equivalent_standard",
		major_differences:
			"VAS 02 cho phép phương pháp LIFO (nhập sau xuất trước) trên nguyên tắc và cho phép hoàn nhập dự phòng giảm giá hàng tồn kho. IAS 2 nghiêm cấm phương pháp LIFO, chỉ chấp nhận FIFO và bình quân gia quyền.",
	},
	{
		topic: "Consolidation",
		vas: "VAS-25",
		ifrs: "IFRS-10",
		ias: "IAS-27",
		relationship: "equivalent_standard",
		major_differences:
			"VAS 25 xác định quyền kiểm soát chủ yếu dựa trên tỷ lệ sở hữu trên 50% quyền biểu quyết theo luật định. IFRS 10 định nghĩa quyền kiểm soát bản chất (de facto control) dựa trên 3 yếu tố: Quyền lực, tiếp xúc với lợi nhuận biến đổi, và khả năng sử dụng quyền lực để tác động đến lợi nhuận.",
	},
	{
		topic: "Impairment of Assets",
		vas: "None",
		ifrs: "IAS-36",
		ias: "IAS-36",
		relationship: "missing_standard",
		major_differences:
			"VAS chưa có chuẩn mực về tổn thất tài sản (Impairment). Tài sản duy trì theo giá gốc trừ khấu hao lũy kế; dự phòng chỉ áp dụng cho hàng tồn kho, đầu tư tài chính và nợ khó đòi. IFRS yêu cầu kiểm tra tổn thất định kỳ hàng năm cho Lợi thế thương mại / TSCĐ vô hình và khi có dấu hiệu suy giảm cho các tài sản khác.",
	},
	{
		topic: "Financial Instruments",
		vas: "None",
		ifrs: "IFRS-9",
		ias: "IAS-39",
		relationship: "missing_standard",
		major_differences:
			"VAS ghi nhận công cụ tài chính theo giá gốc, dự phòng chỉ trích lập khi giá trị thị trường của cổ phiếu niêm yết sụt giảm hoặc nợ quá hạn. IFRS 9 phân loại theo mô hình kinh doanh và dòng tiền hợp đồng (Amortised Cost, FVOCI, FVTPL), áp dụng mô hình tổn thất tín dụng dự kiến (ECL) thay thế mô hình tổn thất đã phát sinh.",
	},
	{
		topic: "Intangible Assets",
		vas: "VAS-04",
		ifrs: "IAS-38",
		ias: "IAS-38",
		relationship: "equivalent_standard",
		major_differences:
			"VAS 04 ghi nhận quyền sử dụng đất lâu dài là TSCĐ vô hình không tính khấu hao. IFRS phân loại quyền sử dụng đất vào tài sản quyền sử dụng theo IFRS 16 hoặc bất động sản đầu tư theo IAS 40. VAS không cho phép mô hình đánh giá lại đối với TSCĐ vô hình.",
	},
];

const FALLBACK_TOPICS = [
	{
		topic_id: "revenue_recognition",
		topic_name: "Doanh thu hợp đồng khách hàng",
		aliases: ["Revenue", "Doanh thu", "Ghi nhận doanh thu"],
		related_topics: ["financial_instruments", "business_combinations"],
	},
	{
		topic_id: "leases",
		topic_name: "Thuê tài sản (Leases)",
		aliases: ["Leases", "Thuê tài sản", "ROU Asset", "Nợ thuê"],
		related_topics: ["property_plant_equipment", "impairment"],
	},
	{
		topic_id: "property_plant_equipment",
		topic_name: "Tài sản cố định & Đánh giá lại",
		aliases: ["PPE", "Tài sản cố định hữu hình", "Revaluation Model"],
		related_topics: ["leases", "intangible_assets", "impairment"],
	},
	{
		topic_id: "inventory",
		topic_name: "Hàng tồn kho & Định giá",
		aliases: ["Inventory", "Hàng tồn kho", "FIFO", "LIFO"],
		related_topics: ["property_plant_equipment", "impairment"],
	},
	{
		topic_id: "impairment",
		topic_name: "Tổn thất tài sản (Impairment)",
		aliases: ["Impairment", "Tổn thất tài sản", "IAS 36", "Suy giảm giá trị"],
		related_topics: ["property_plant_equipment", "intangible_assets"],
	},
	{
		topic_id: "financial_instruments",
		topic_name: "Công cụ tài chính & Dự phòng ECL",
		aliases: ["Financial Instruments", "IFRS 9", "ECL", "Fair value"],
		related_topics: ["revenue_recognition", "impairment"],
	},
	{
		topic_id: "consolidation",
		topic_name: "Hợp nhất Báo cáo tài chính",
		aliases: ["Consolidation", "BCTC hợp nhất", "Kiểm soát bản chất"],
		related_topics: ["business_combinations"],
	},
];

const FALLBACK_DATA: StandardsData = {
	vas_standards: FALLBACK_VAS_STANDARDS,
	ifrs_standards: FALLBACK_IFRS_STANDARDS,
	relations: FALLBACK_RELATIONS,
	topics: FALLBACK_TOPICS,
};

export async function GET() {
	try {
		const upstream = await authenticatedBackendFetch("/v1/kb/standards");
		if (upstream.ok) {
			const data = (await upstream.json()) as StandardsData;
			return NextResponse.json(data);
		}
		console.warn(
			`Upstream /v1/kb/standards returned ${upstream.status}. Using fallback standards data.`,
		);
		return NextResponse.json(FALLBACK_DATA);
	} catch (error) {
		console.warn(
			"Backend request for /v1/kb/standards failed. Using fallback data.",
			error,
		);
		return NextResponse.json(FALLBACK_DATA);
	}
}
