# Danh sách công việc

| Bước | Phạm vi | Tiêu chí và cách kiểm chứng | Phụ thuộc |
| --- | --- | --- | --- |
| 0 | Đo baseline | Đã đo [VAS local trên 6 câu holdout](../ingestion/sources/evaluation/VAS_BENCHMARK.md), lưu chất lượng, độ trễ, token và kết quả từng câu. Còn baseline VAS–IFRS với stack triển khai và tập test đã rà soát độc lập. | Corpus được phép dùng và môi trường eval |
| 1 | Retrieval giữ đủ nội dung chunk | Bản sửa cục bộ đạt 5/5 ca hồi quy so với 2/5 tại baseline. Cần đo E − D trên corpus thật để quyết định theo chất lượng và chi phí. | 0 |
| 2 | Citation sau retry | Đã xác minh citation không tồn tại bị loại khỏi `final` và nội dung lưu. Marker hợp lệ trong nhóm được giữ. | 1 |
| 3 | Search khi dịch vụ lỗi | Đã xác minh Chat và Compare qua HTTP SSE khi kết quả rỗng, lỗi một phần và lỗi toàn bộ. | 1 |
| 4 | CORS và session | Đã xác minh CORS, JWT, RBAC, PostgREST RLS và đăng nhập, tải lại, đăng xuất của hai tenant qua trình duyệt local. | — |
| 5 | Ingestion và khôi phục | Đã xác minh upload `.txt` tới `ready`, tìm lại qua Qdrant và tự khôi phục sau khi worker bị dừng. Replay cùng document ID giữ nguyên số điểm. | 1, 4 |
| 6 | Đo RAG và UX | Đã đo 3 cặp QA VAS Việt–Anh và kiểm tra Chat/Compare local khi ngắt stream, thiếu nguồn, lỗi provider và đọc lại lịch sử. | 2, 3, 5 |
| 7 | Parser Trial Balance | Đã xác minh CSV/XLSX giữ đúng mã, đầu kỳ, phát sinh và cuối kỳ. Bộ đọc từ chối header mơ hồ và số tiền không hợp lệ. Cả 8 tài khoản trong mẫu ứng dụng qua `parse_gl_file`. | — |
| 8 | Mapping và bút toán | Đã xác minh quy tắc theo tenant, số tiền Decimal hữu hạn, cân bằng Nợ/Có và giữ phân bổ từng dòng trước phê duyệt. | 4, 7 |
| 9 | Nối từng chặng GL | Đã xác minh upload → mapping → bút toán → duyệt → xuất bảng cân đối phát sinh sau điều chỉnh trên API/Postgres và Chromium/Supabase local. Có kiểm thử retry, phân quyền và nhật ký thao tác. | 8 |
| 10 | CI, hạ tầng và vận hành | Đã cập nhật CI, migration khi khởi động Compose và runbook. Kiểm chứng cục bộ migration/rollback, build, phục hồi GL, Kustomize, Terraform, Supabase và MCP. Staging và production chưa được chạy triển khai. | 4, 5, 6, 9 |

- [x] Sau bước 3, kiểm chứng Chat/Compare với nguồn hợp lệ, nguồn thiếu và dependency lỗi.
- [x] Pilot LoRA có baseline trước train, train/dev/test tách biệt và 4/4 cấu hình trên test khóa. [Kết quả pilot](../ingestion/sources/evaluation/matrix-v1/README.md)
- [ ] Benchmark VAS–IFRS đầu cuối với corpus toàn văn được cấp quyền, chấm độc lập và câu trả lời tự do.
- [x] Sau bước 6, ghi lại kết quả kiểm thử tích hợp và mức chất lượng RAG đo được.
- [x] Sau bước 10, tổng hợp phần đã xác minh, phần còn thiếu và rủi ro vận hành trong [bản đánh giá](evaluation.md).

## Đợt Chat và Compare

- [x] Tái hiện lỗi citation sau retry, marker nhóm và trường hợp truy xuất thất bại toàn bộ.
- [x] Sửa citation và phân biệt lỗi truy xuất với kết quả rỗng.
- [x] Chạy test hồi quy và xác minh SSE, Postgres trên stack local.

## Compare theo bằng chứng

- [x] Khóa bộ câu mới, đo Compare hiện hành và chấm cùng rubric.
- [x] Thêm chế độ trích đoạn dùng chung truy xuất, citation và SSE, có kiểm thử nguồn thiếu và dữ liệu không tin cậy.
- [x] Đo lại, ghi độ trễ và mức hỗ trợ nghiệp vụ, quyết định cấu hình mặc định và staging.
