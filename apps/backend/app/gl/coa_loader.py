"""Chart of accounts loader for VAS standard COA."""

from __future__ import annotations

from typing import Any

# Standard VAS Circular 200 Chart of Accounts (main accounts)
_VAS_CIRCULAR_200_COA: dict[str, dict[str, Any]] = {
    "111": {
        "name_vi": "Tiền mặt",
        "name_en": "Cash",
        "category": "Asset",
        "ifrs_equivalent": "Cash and Cash Equivalents",
    },
    "112": {
        "name_vi": "Tiền gửi Ngân hàng",
        "name_en": "Cash in Bank",
        "category": "Asset",
        "ifrs_equivalent": "Cash and Cash Equivalents",
    },
    "121": {
        "name_vi": "Chứng khoán kinh doanh",
        "name_en": "Trading Securities",
        "category": "Asset",
        "ifrs_equivalent": "Financial Assets at Fair Value through Profit or Loss",
    },
    "128": {
        "name_vi": "Đầu tư nắm giữ đến ngày đáo hạn",
        "name_en": "Held-to-maturity Investments",
        "category": "Asset",
        "ifrs_equivalent": "Amortized Cost Financial Assets",
    },
    "131": {
        "name_vi": "Phải thu của khách hàng",
        "name_en": "Trade Receivables",
        "category": "Asset",
        "ifrs_equivalent": "Trade and Other Receivables",
    },
    "138": {
        "name_vi": "Phải thu khác",
        "name_en": "Other Receivables",
        "category": "Asset",
        "ifrs_equivalent": "Trade and Other Receivables",
    },
    "141": {
        "name_vi": "Tạm ứng",
        "name_en": "Advances",
        "category": "Asset",
        "ifrs_equivalent": "Trade and Other Receivables",
    },
    "152": {
        "name_vi": "Nguyên liệu, vật liệu",
        "name_en": "Raw Materials",
        "category": "Asset",
        "ifrs_equivalent": "Inventories",
    },
    "153": {
        "name_vi": "Công cụ, dụng cụ",
        "name_en": "Tools and Supplies",
        "category": "Asset",
        "ifrs_equivalent": "Inventories",
    },
    "156": {
        "name_vi": "Hàng hóa",
        "name_en": "Merchandise",
        "category": "Asset",
        "ifrs_equivalent": "Inventories",
    },
    "211": {
        "name_vi": "Tài sản cố định hữu hình",
        "name_en": "Tangible Fixed Assets",
        "category": "Asset",
        "ifrs_equivalent": "Property, Plant and Equipment",
    },
    "213": {
        "name_vi": "Tài sản cố định vô hình",
        "name_en": "Intangible Fixed Assets",
        "category": "Asset",
        "ifrs_equivalent": "Intangible Assets",
    },
    "214": {
        "name_vi": "Hao mòn tài sản cố định",
        "name_en": "Accumulated Depreciation",
        "category": "Asset",
        "ifrs_equivalent": "Property, Plant and Equipment",
    },
    "229": {
        "name_vi": "Dự phòng tổn thất tài sản",
        "name_en": "Provisions for Asset Impairment",
        "category": "Asset",
        "ifrs_equivalent": "Impairment Allowance",
    },
    "241": {
        "name_vi": "Chi phí xây dựng cơ bản dở dang",
        "name_en": "Construction in Progress",
        "category": "Asset",
        "ifrs_equivalent": "Property, Plant and Equipment",
    },
    "242": {
        "name_vi": "Chi phí trả trước",
        "name_en": "Prepaid Expenses",
        "category": "Asset",
        "ifrs_equivalent": "Prepaid Expenses / Right-of-Use Assets",
    },
    "331": {
        "name_vi": "Phải trả cho người bán",
        "name_en": "Trade Payables",
        "category": "Liability",
        "ifrs_equivalent": "Trade and Other Payables",
    },
    "333": {
        "name_vi": "Thuế và các khoản phải nộp Nhà nước",
        "name_en": "Taxes and Other Payables to State",
        "category": "Liability",
        "ifrs_equivalent": "Current Tax Liabilities",
    },
    "334": {
        "name_vi": "Phải trả người lao động",
        "name_en": "Payables to Employees",
        "category": "Liability",
        "ifrs_equivalent": "Employee Benefits Liabilities",
    },
    "338": {
        "name_vi": "Phải trả, phải nộp khác",
        "name_en": "Other Payables",
        "category": "Liability",
        "ifrs_equivalent": "Trade and Other Payables",
    },
    "341": {
        "name_vi": "Vay và nợ thuê tài chính",
        "name_en": "Borrowings and Finance Lease Liabilities",
        "category": "Liability",
        "ifrs_equivalent": "Borrowings / Lease Liabilities",
    },
    "352": {
        "name_vi": "Dự phòng phải trả",
        "name_en": "Provisions for Payables",
        "category": "Liability",
        "ifrs_equivalent": "Provisions",
    },
    "411": {
        "name_vi": "Vốn góp của chủ sở hữu",
        "name_en": "Share Capital",
        "category": "Equity",
        "ifrs_equivalent": "Share Capital",
    },
    "421": {
        "name_vi": "Lợi nhuận sau thuế chưa phân phối",
        "name_en": "Retained Earnings",
        "category": "Equity",
        "ifrs_equivalent": "Retained Earnings",
    },
    "511": {
        "name_vi": "Doanh thu bán hàng và cung cấp dịch vụ",
        "name_en": "Revenue from Sales and Services",
        "category": "Revenue",
        "ifrs_equivalent": "Revenue from Contracts with Customers",
    },
    "515": {
        "name_vi": "Doanh thu hoạt động tài chính",
        "name_en": "Financial Revenue",
        "category": "Revenue",
        "ifrs_equivalent": "Finance Income",
    },
    "632": {
        "name_vi": "Giá vốn hàng bán",
        "name_en": "Cost of Goods Sold",
        "category": "Expense",
        "ifrs_equivalent": "Cost of Sales",
    },
    "635": {
        "name_vi": "Chi phí tài chính",
        "name_en": "Financial Expenses",
        "category": "Expense",
        "ifrs_equivalent": "Finance Costs",
    },
    "641": {
        "name_vi": "Chi phí bán hàng",
        "name_en": "Selling Expenses",
        "category": "Expense",
        "ifrs_equivalent": "Selling and Distribution Expenses",
    },
    "642": {
        "name_vi": "Chi phí quản lý doanh nghiệp",
        "name_en": "General and Administrative Expenses",
        "category": "Expense",
        "ifrs_equivalent": "General and Administrative Expenses",
    },
    "711": {
        "name_vi": "Thu nhập khác",
        "name_en": "Other Income",
        "category": "Revenue",
        "ifrs_equivalent": "Other Income",
    },
    "811": {
        "name_vi": "Chi phí khác",
        "name_en": "Other Expenses",
        "category": "Expense",
        "ifrs_equivalent": "Other Expenses",
    },
    "911": {
        "name_vi": "Xác định kết quả kinh doanh",
        "name_en": "Net Income Determination",
        "category": "Equity",
        "ifrs_equivalent": "Profit or Loss Summary",
    },
}


def load_coa(standard: str = "VAS") -> dict[str, dict[str, Any]]:
    """Return a mapping of account codes to their metadata for the given standard."""
    if standard.upper() == "VAS":
        return _VAS_CIRCULAR_200_COA
    # Add other standards if needed in the future
    return {}
