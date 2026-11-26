export const SAMPLE_TB_ROWS = [
	{
		code: "1111",
		name: "Tiền mặt Việt Nam đồng",
		openDr: "1,250,000,000",
		openCr: "0",
		movDr: "8,450,000,000",
		movCr: "8,100,000,000",
		closeDr: "1,600,000,000",
		closeCr: "0",
	},
	{
		code: "1121",
		name: "Tiền gửi Ngân hàng thương mại",
		openDr: "14,820,000,000",
		openCr: "0",
		movDr: "42,100,000,000",
		movCr: "39,500,000,000",
		closeDr: "17,420,000,000",
		closeCr: "0",
	},
	{
		code: "131",
		name: "Phải thu của khách hàng",
		openDr: "32,450,000,000",
		openCr: "0",
		movDr: "68,200,000,000",
		movCr: "64,150,000,000",
		closeDr: "36,500,000,000",
		closeCr: "0",
	},
	{
		code: "1561",
		name: "Giá mua hàng hóa",
		openDr: "18,900,000,000",
		openCr: "0",
		movDr: "54,200,000,000",
		movCr: "51,800,000,000",
		closeDr: "21,300,000,000",
		closeCr: "0",
	},
	{
		code: "2111",
		name: "Nhà cửa, vật kiến trúc",
		openDr: "58,000,000,000",
		openCr: "0",
		movDr: "0",
		movCr: "0",
		closeDr: "58,000,000,000",
		closeCr: "0",
	},
	{
		code: "2141",
		name: "Hao mòn TSCĐ hữu hình",
		openDr: "0",
		openCr: "16,400,000,000",
		movDr: "0",
		movCr: "2,900,000,000",
		closeDr: "0",
		closeCr: "19,300,000,000",
	},
	{
		code: "2293",
		name: "Dự phòng phải thu khó đòi",
		openDr: "0",
		openCr: "850,000,000",
		movDr: "150,000,000",
		movCr: "300,000,000",
		closeDr: "0",
		closeCr: "1,000,000,000",
	},
	{
		code: "3411",
		name: "Vay và nợ thuê tài chính",
		openDr: "0",
		openCr: "22,000,000,000",
		movDr: "5,000,000,000",
		movCr: "8,000,000,000",
		closeDr: "0",
		closeCr: "25,000,000,000",
	},
];

export function downloadTrialBalanceTemplate() {
	const headers =
		"Mã TK,Tên Tài Khoản,Dư Đầu Kỳ Nợ,Dư Đầu Kỳ Có,Phát Sinh Nợ,Phát Sinh Có,Dư Cuối Kỳ Nợ,Dư Cuối Kỳ Có\n";
	const rows = SAMPLE_TB_ROWS.map(
		(r) =>
			`"${r.code}","${r.name}",${r.openDr.replace(/,/g, "")},${r.openCr.replace(/,/g, "")},${r.movDr.replace(/,/g, "")},${r.movCr.replace(/,/g, "")},${r.closeDr.replace(/,/g, "")},${r.closeCr.replace(/,/g, "")}`,
	).join("\n");
	const csvContent = `\uFEFF${headers}${rows}`;
	const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
	const url = URL.createObjectURL(blob);
	const link = document.createElement("a");
	link.setAttribute("href", url);
	link.setAttribute(
		"download",
		"VAS_Trial_Balance_Sample_TT200_VAS_IFRS_Bridge.csv",
	);
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url);
}
