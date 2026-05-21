# VAS-IFRS Bridge TODO List

Dưới đây là danh sách các tác vụ (todo list) để sửa lỗi và hoàn thiện codebase dựa trên kết quả review.

## Danh sách Task

### [x] Task 1: Sửa lỗi Import Typo `BaseAgent` -> `AgentBase` (Mức độ ưu tiên: Cao)
- [x] Sửa file `apps/backend/app/agents/gl_mapping_agent.py`
- [x] Sửa file `apps/backend/app/agents/adjustment_agent.py`
- [x] Sửa file `apps/backend/app/agents/report_agent.py`
- [x] Kiểm chứng (Verify) bằng cách import thử qua Python CLI

### [x] Task 2: Hiện thực hóa GL Mapping Agent cơ bản (`GLMappingAgent`)
- [x] Cập nhật file `apps/backend/app/agents/gl_mapping_agent.py` với logic gọi Gemini hoặc so khớp luật cơ bản
- [x] Kiểm tra chạy thử bằng file script thử nghiệm

### [x] Task 3: Thêm Unit Test cơ bản
- [x] Tạo file `apps/backend/tests/unit/test_agents.py`
- [x] Viết test case cho `AgentBase`, `RetrievalAgent` và `IFRSCompareAgent`
- [x] Chạy bộ test suite bằng `pytest`

### [x] Task 4: Thiết kế và Hiện thực hóa `AdjustmentAgent`
- [x] Xây dựng prompt sinh bút toán điều chỉnh nợ/có cân bằng (IFRS Adjustment JEs)
- [x] Implement hàm `arun` với Gemini LLM stream và CitationValidator trong `adjustment_agent.py`
- [x] Tích hợp `AdjustmentAgent` vào luồng orchestrator

### [x] Task 5: Triển khai logic tính toán & kiểm tra cân bằng (`app/gl/adjustments.py`)
- [x] Hoàn thiện hàm `generate_entries(mapping_results: list[dict]) -> list[dict]` trong `app/gl/adjustments.py` để trích xuất JSON bút toán từ LLM response.
- [x] Thực hiện kiểm tra tính cân bằng Nợ = Có và ném lỗi `UnbalancedJE` nếu mất cân đối.

### [x] Task 6: Hoàn thiện Tool Wrapper (`app/tools/generate_adjustment.py`)
- [x] Implement hàm `generate_adjustment(mapping_id: str) -> dict` để gọi logic sinh bút toán điều chỉnh.

### [x] Task 7: Triển khai API Endpoints đầy đủ (`app/api/v1/adjustments.py`)
- [x] Triển khai endpoint `/` để truy vấn danh sách bút toán điều chỉnh.
- [x] Triển khai endpoint `/{entry_id}/approve` để đánh dấu đã phê duyệt và log audit.

### [x] Task 8: Mở rộng bộ Unit Test & Chạy kiểm thử
- [x] Thêm các test case kiểm tra `AdjustmentAgent` hoạt động với mock LLM.
- [x] Thêm test case xác thực hàm `validate_balance` ném ngoại lệ `UnbalancedJE` khi bị mất cân đối.
- [x] Chạy bộ test suite bằng `pytest` đạt kết quả 100% Passed.
