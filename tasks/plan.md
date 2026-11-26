# Kế hoạch đánh giá lại và cải tiến VAS-IFRS Bridge

Dùng [kết quả rà soát hiện có](../docs/PROJECT_REVIEW.md) làm điểm xuất phát. Đối chiếu tài liệu với code, cấu hình triển khai và hành vi đo được. Ghi rõ bằng chứng nào đến từ test giả lập, môi trường tích hợp hoặc đọc code. Theo dõi từng bước trong [danh sách công việc](todo.md).

Áp dụng [quy trình evaluation](evaluation.md) trước các thay đổi tiếp theo. Đóng băng baseline model gốc và pipeline tại SHA đã ghi, đo trên cùng test set, sau đó thay một thành phần mỗi lượt. Đo fine-tuning riêng bằng cặp checkpoint gốc và đã train.

1. Xác nhận lại các lỗi đã tái hiện và sửa từng điểm ảnh hưởng luồng đang chạy. Bắt đầu với dữ liệu nguồn bị cắt trong Chat và Compare, sau đó xử lý citation, lỗi dependency và CORS.
2. Kiểm tra các luồng đang vận hành từ phía người dùng đến nơi lưu dữ liệu. Bao gồm đăng nhập, phân quyền tenant, lịch sử chat, Compare, upload tài liệu, indexing, các dịch vụ embedding và reranking. Kiểm thử dữ liệu giả ở local hoặc staging.
3. Đánh giá các luồng GL theo thứ tự phụ thuộc: nhập Trial Balance, mapping, bút toán, phê duyệt và báo cáo. Chốt schema và bộ ví dụ đầu vào/đầu ra trước khi nối từng chặng. Phân biệt mức độ sẵn sàng của sandbox, module nội bộ và API.
4. Đối chiếu CI, Docker, Kubernetes, Terraform, Supabase và MCP/n8n với các luồng thực tế. Kiểm chứng build, migrations, readiness, quyền truy cập, phục hồi khi dịch vụ gián đoạn và cách rollback.

Mỗi bước bắt đầu bằng một tình huống kiểm thử có kết quả mong đợi, kết thúc bằng kiểm tra hồi quy và cập nhật trạng thái. Đo lại recall@k, độ chính xác của citation và độ trễ trên cùng bộ câu hỏi và chỉ mục khi có môi trường tích hợp. Dùng fixture kế toán đã đối chiếu để kiểm tra luồng GL trước khi đưa dữ liệu nghiệp vụ vào.

## Đợt kiểm chứng độ tin cậy của Chat và Compare

Tiếp tục bước 2 và 3 trong danh sách công việc sau benchmark 24 câu. Dùng fixture để đo lỗi có đầu ra kiểm chứng được. Giữ benchmark chất lượng model và dữ liệu nguồn đã khóa.

1. Thêm ca hồi quy trước sửa. Kiểm tra marker đơn và nhóm, nội dung sau khi Chat thử lại, và ba trạng thái truy xuất thành công rỗng, lỗi một phần và lỗi toàn bộ.
2. Đồng nhất cách đọc và loại marker citation. Kiểm tra lại câu trả lời sau retry; nếu retry không sinh nội dung thì giữ bản đầu đã làm sạch. Kiểm tra Compare dùng cùng bộ lọc.
3. Báo lỗi SSE khi tất cả truy xuất cần thiết thất bại và không có bằng chứng graph. Giữ khả năng trả lời từ nguồn còn hoạt động khi lỗi một phần. Dùng thông báo lỗi an toàn đã định dạng theo ngôn ngữ API để frontend hiển thị.
4. Chạy test tập trung, bộ unit test backend và smoke HTTP SSE trên stack local. Dùng đầu ra model kiểm soát được cho ca citation và lỗi dependency mô phỏng trong tiến trình benchmark; đối chiếu đầu ra SSE với lịch sử Postgres. Ghi số test trước/sau và phạm vi đã kiểm chứng.

## Tối ưu Compare sau đánh giá bộ kiểm tra nhận định

1. Khóa tập câu tự do mới và tiêu chí đo trước khi đổi Compare. Đo lại phiên bản hiện hành bằng cùng Qwen và chỉ mục local. Chấm riêng câu trả lời đúng, đoạn nguồn phù hợp và việc từ chối nguồn thiếu.
2. Thêm chế độ Compare chỉ hiển thị bằng chứng. Dùng lại truy xuất theo chuẩn, scope và citation hiện có. Lấy đoạn đầu mỗi chuẩn từ kết quả đã xếp hạng, ghi rõ đây là trích đoạn để đối chiếu, rồi báo phần không tìm thấy. Không gọi model sinh kết luận ở chế độ này. Giữ giao thức SSE cho UI và lịch sử, không đưa bộ kiểm tra nhận định v4 vào đường phục vụ.
3. Kiểm thử các ranh giới dữ liệu và chạy đối chứng trên tập khóa. Kiểm tra căn cứ cho hai phía, nhầm mã, dữ liệu tenant, lỗi truy xuất và an toàn khi nội dung nguồn chứa chuỗi giống citation. Đo độ trễ và chấm đọc hiểu nghiệp vụ trước khi đề xuất thay cấu hình mặc định hoặc staging.
4. Giữ phần trích dẫn và phần trả lời tổng hợp có vai trò rõ ràng. Nếu chế độ bằng chứng chỉ giúp rà soát, ghi rõ giới hạn và giữ nó ở dạng opt-in. Chưa coi phép đo trên 18 thẻ là bằng chứng đủ để phát hành tư vấn tự động.
