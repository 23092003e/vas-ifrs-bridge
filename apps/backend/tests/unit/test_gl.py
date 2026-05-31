"""Unit tests for General Ledger processing modules."""

from __future__ import annotations

import csv
import tempfile
from unittest.mock import patch
import pytest

from app.gl.coa_loader import load_coa
from app.gl.parser import parse
from app.gl.mapping_engine import map_accounts


def test_coa_loader():
    """Verify standard VAS Circular 200 COA is loaded with correct keys and values."""
    coa = load_coa("VAS")
    assert isinstance(coa, dict)
    assert "111" in coa
    assert coa["111"]["name_vi"] == "Tiền mặt"
    assert coa["111"]["category"] == "Asset"
    assert coa["111"]["ifrs_equivalent"] == "Cash and Cash Equivalents"


def test_parser_csv():
    """Verify parse() reads and normalizes CSV data correctly."""
    csv_content = [
        ["Số hiệu tài khoản", "Tên tài khoản", "Nợ phát sinh", "Có phát sinh"],
        ["1111", "Tiền mặt tại quỹ", "5000000", "0"],
        ["1121", "Tiền gửi ngân hàng", "0", "12000000"],
        ["242", "Chi phí trả trước ngắn hạn", "0", "0"],  # Should default balance to 0
    ]

    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".csv", delete=False, encoding="utf-8-sig"
    ) as tmp:
        writer = csv.writer(tmp)
        writer.writerows(csv_content)
        tmp_name = tmp.name

    try:
        results = parse(tmp_name)
        assert len(results) == 3

        # Test 1111
        r0 = next(r for r in results if r["account_code"] == "1111")
        assert r0["account_name"] == "Tiền mặt tại quỹ"
        assert r0["debit"] == 5000000.0
        assert r0["credit"] == 0.0
        assert r0["balance"] == 5000000.0

        # Test 1121
        r1 = next(r for r in results if r["account_code"] == "1121")
        assert r1["account_name"] == "Tiền gửi ngân hàng"
        assert r1["debit"] == 0.0
        assert r1["credit"] == 12000000.0
        assert r1["balance"] == -12000000.0

    finally:
        import os

        os.remove(tmp_name)


@pytest.mark.asyncio
async def test_mapping_engine_rules():
    """Verify map_accounts maps standard prefixes without calling LLM."""
    accounts = [
        {"account_code": "1111", "account_name": "Tiền mặt VNĐ"},
        {"account_code": "1122", "account_name": "Tiền gửi USD"},
        {"account_code": "2421", "account_name": "Chi phí trả trước dài hạn"},
    ]

    # These codes all map to prefixes in load_coa: 111, 112, 242. No LLM should be called.
    with patch("app.gl.mapping_engine._map_with_llm") as mock_llm:
        results = await map_accounts(accounts, tenant_id="test-tenant")

        assert len(results) == 3
        mock_llm.assert_not_called()

        r0 = next(r for r in results if r["src_account_code"] == "1111")
        assert r0["target_account_name"] == "Cash and Cash Equivalents"
        assert r0["confidence"] == 0.95

        r1 = next(r for r in results if r["src_account_code"] == "1122")
        assert r1["target_account_name"] == "Cash and Cash Equivalents"

        r2 = next(r for r in results if r["src_account_code"] == "2421")
        assert r2["target_account_name"] == "Prepaid Expenses / Right-of-Use Assets"


@pytest.mark.asyncio
@patch("app.gl.mapping_engine._map_with_llm")
async def test_mapping_engine_fallback(mock_llm):
    """Verify map_accounts falls back to LLM for unknown accounts."""
    accounts = [
        {"account_code": "1111", "account_name": "Tiền mặt"},  # Rule matches (111)
        {"account_code": "999", "account_name": "Tài khoản lạ hoắc"},  # Rule doesn't match
    ]

    # Mock the LLM return value for 999
    mock_llm.return_value = [
        {
            "src_account_code": "999",
            "src_account_name": "Tài khoản lạ hoắc",
            "target_standard": "IFRS",
            "target_account_code": "OTHER_FINANCIAL_ASSETS",
            "target_account_name": "Other Financial Assets",
            "confidence": 0.85,
            "rationale": "LLM mapping fallback",
        }
    ]

    results = await map_accounts(accounts, tenant_id="test-tenant")
    assert len(results) == 2
    mock_llm.assert_called_once_with([{"account_code": "999", "account_name": "Tài khoản lạ hoắc"}])

    r_rule = next(r for r in results if r["src_account_code"] == "1111")
    assert r_rule["target_account_name"] == "Cash and Cash Equivalents"
    assert r_rule["confidence"] == 0.95

    r_llm = next(r for r in results if r["src_account_code"] == "999")
    assert r_llm["target_account_name"] == "Other Financial Assets"
    assert r_llm["confidence"] == 0.85
