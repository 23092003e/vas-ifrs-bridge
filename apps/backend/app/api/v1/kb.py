"""Knowledge base management endpoints."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.rag.retriever import _qdrant_client

logger = logging.getLogger(__name__)
router = APIRouter()

_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
_ONTOLOGY_DIR = _REPO_ROOT / "ingestion" / "metadata" / "ontology"

DEFAULT_VAS_STANDARDS = [
    {"code": "VAS-01", "name": "Chuẩn mực chung (Framework)", "category": "General"},
    {"code": "VAS-02", "name": "Hàng tồn kho (Inventories)", "category": "Assets"},
    {"code": "VAS-03", "name": "Tài sản cố định hữu hình (PPE)", "category": "Assets"},
    {"code": "VAS-04", "name": "Tài sản cố định vô hình (Intangibles)", "category": "Assets"},
    {"code": "VAS-05", "name": "Bất động sản đầu tư (Investment Property)", "category": "Assets"},
    {"code": "VAS-06", "name": "Thuê tài sản (Leases)", "category": "Liabilities"},
    {"code": "VAS-07", "name": "Kế toán các khoản đầu tư vào công ty liên kết", "category": "Investments"},
    {"code": "VAS-08", "name": "Thông tin tài chính về những khoản vốn góp liên doanh", "category": "Investments"},
    {"code": "VAS-10", "name": "Ảnh hưởng của việc thay đổi tỷ giá hối đoái", "category": "Foreign Exchange"},
    {"code": "VAS-11", "name": "Hợp nhất kinh doanh (Business Combinations)", "category": "Group"},
    {"code": "VAS-14", "name": "Doanh thu và thu nhập khác (Revenue)", "category": "Income"},
    {"code": "VAS-15", "name": "Hợp đồng xây dựng (Construction Contracts)", "category": "Income"},
    {"code": "VAS-16", "name": "Chi phí đi vay (Borrowing Costs)", "category": "Expenses"},
    {"code": "VAS-17", "name": "Thuế thu nhập doanh nghiệp (Income Taxes)", "category": "Taxes"},
    {"code": "VAS-18", "name": "Các khoản dự phòng, tài sản và nợ tiềm tàng", "category": "Liabilities"},
    {"code": "VAS-21", "name": "Trình bày báo cáo tài chính", "category": "Presentation"},
    {"code": "VAS-22", "name": "Trình bày bổ sung BCTC của các ngân hàng và TCTD", "category": "Presentation"},
    {"code": "VAS-23", "name": "Các sự kiện phát sinh sau ngày kết thúc kỳ kế toán năm", "category": "General"},
    {"code": "VAS-24", "name": "Báo cáo lưu chuyển tiền tệ (Cash Flows)", "category": "Presentation"},
    {"code": "VAS-25", "name": "Báo cáo tài chính hợp nhất và kế toán khoản đầu tư vào cty con", "category": "Group"},
    {"code": "VAS-26", "name": "Thông tin về các bên liên quan (Related Parties)", "category": "Disclosure"},
    {"code": "VAS-27", "name": "Báo cáo tài chính giữa niên độ", "category": "Presentation"},
    {"code": "VAS-28", "name": "Báo cáo bộ phận (Segment Reporting)", "category": "Disclosure"},
    {"code": "VAS-29", "name": "Thay đổi chính sách kế toán, ước tính kế toán và các sai sót", "category": "General"},
    {"code": "VAS-30", "name": "Lãi trên cổ phiếu (Earnings per Share)", "category": "Presentation"},
    {"code": "TT-200", "name": "Thông tư 200/2014/TT-BTC Chế độ kế toán doanh nghiệp", "category": "Circulars"},
]

DEFAULT_IFRS_STANDARDS = [
    {"code": "IFRS-1", "name": "First-time Adoption of IFRS", "category": "First-time"},
    {"code": "IFRS-2", "name": "Share-based Payment", "category": "Expenses"},
    {"code": "IFRS-3", "name": "Business Combinations", "category": "Group"},
    {"code": "IFRS-5", "name": "Non-current Assets Held for Sale and Discontinued Operations", "category": "Assets"},
    {"code": "IFRS-7", "name": "Financial Instruments: Disclosures", "category": "Financial Instruments"},
    {"code": "IFRS-8", "name": "Operating Segments", "category": "Disclosure"},
    {"code": "IFRS-9", "name": "Financial Instruments", "category": "Financial Instruments"},
    {"code": "IFRS-10", "name": "Consolidated Financial Statements", "category": "Group"},
    {"code": "IFRS-11", "name": "Joint Arrangements", "category": "Group"},
    {"code": "IFRS-12", "name": "Disclosure of Interests in Other Entities", "category": "Disclosure"},
    {"code": "IFRS-13", "name": "Fair Value Measurement", "category": "Measurement"},
    {"code": "IFRS-15", "name": "Revenue from Contracts with Customers", "category": "Income"},
    {"code": "IFRS-16", "name": "Leases", "category": "Liabilities"},
    {"code": "IAS-1", "name": "Presentation of Financial Statements", "category": "Presentation"},
    {"code": "IAS-2", "name": "Inventories", "category": "Assets"},
    {"code": "IAS-7", "name": "Statement of Cash Flows", "category": "Presentation"},
    {"code": "IAS-8", "name": "Accounting Policies, Changes in Accounting Estimates and Errors", "category": "General"},
    {"code": "IAS-12", "name": "Income Taxes", "category": "Taxes"},
    {"code": "IAS-16", "name": "Property, Plant and Equipment", "category": "Assets"},
    {"code": "IAS-19", "name": "Employee Benefits", "category": "Expenses"},
    {"code": "IAS-20", "name": "Accounting for Government Grants", "category": "Income"},
    {"code": "IAS-21", "name": "The Effects of Changes in Foreign Exchange Rates", "category": "Foreign Exchange"},
    {"code": "IAS-23", "name": "Borrowing Costs", "category": "Expenses"},
    {"code": "IAS-24", "name": "Related Party Disclosures", "category": "Disclosure"},
    {"code": "IAS-27", "name": "Separate Financial Statements", "category": "Group"},
    {"code": "IAS-28", "name": "Investments in Associates and Joint Ventures", "category": "Group"},
    {"code": "IAS-32", "name": "Financial Instruments: Presentation", "category": "Financial Instruments"},
    {"code": "IAS-36", "name": "Impairment of Assets", "category": "Assets"},
    {"code": "IAS-37", "name": "Provisions, Contingent Liabilities and Contingent Assets", "category": "Liabilities"},
    {"code": "IAS-38", "name": "Intangible Assets", "category": "Assets"},
    {"code": "IAS-40", "name": "Investment Property", "category": "Assets"},
]


def _read_json_file(file_path: Path) -> list[dict[str, Any]]:
    if file_path.exists():
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to read JSON %s: %s", file_path, exc)
    return []


@router.get("/collections")
async def list_collections() -> dict[str, Any]:
    """List available knowledge base collections and metrics."""
    client = _qdrant_client()
    try:
        resp = await client.get_collections()
        collections_info = []
        for c in resp.collections:
            points_count = 0
            status = "active"
            try:
                info = await client.get_collection(c.name)
                points_count = info.points_count or 0
                status = str(info.status) if hasattr(info, "status") else "green"
            except Exception as e:  # noqa: BLE001
                logger.debug("Failed to get point count for collection %s: %s", c.name, e)

            collections_info.append({
                "name": c.name,
                "points_count": points_count,
                "status": status,
            })
        return {"collections": collections_info}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Qdrant unavailable: %s. Returning default collection catalog.", exc)
        return {
            "collections": [
                {"name": "kb_shared_vas", "points_count": 0, "status": "active"},
                {"name": "kb_shared_ifrs", "points_count": 0, "status": "active"},
                {"name": "kb_shared_guidance", "points_count": 0, "status": "active"},
                {"name": "kb_shared_mapping", "points_count": 0, "status": "active"},
            ]
        }
    finally:
        await client.close()


@router.get("/standards")
async def list_standards() -> dict[str, Any]:
    """Return categorized standard lists and pre-mapped relations for comparison."""
    relations = _read_json_file(_ONTOLOGY_DIR / "vas_ifrs_relations.json")
    topics = _read_json_file(_ONTOLOGY_DIR / "accounting_topics.json")

    return {
        "vas_standards": DEFAULT_VAS_STANDARDS,
        "ifrs_standards": DEFAULT_IFRS_STANDARDS,
        "relations": relations,
        "topics": topics,
    }
