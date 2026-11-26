# Compare hiển thị trích đoạn nguồn

## Thay đổi

Chế độ `COMPARE_MODE=evidence` dùng truy xuất theo từng chuẩn, bộ lọc tenant và citation hiện có. Luồng trả tối đa một đoạn đã xếp hạng cho mỗi chuẩn được hỏi, hoặc một đoạn mỗi phía khi hỏi chung. Nhãn trích đoạn phân biệt bằng chứng với câu trả lời tự động. Khi thiếu một mã, kết quả giữ đoạn phía còn nguồn và nêu mã còn thiếu. Khi thiếu cả hai, chỉ trả thông báo.

Đoạn được trả nguyên ngôn ngữ nguồn. Chuỗi giống mã citation bên trong tài liệu được hiển thị như văn bản để tránh liên kết nhầm. Trả sự kiện SSE cùng định dạng của Compare. Chế độ này bỏ lượt sinh model. Mặc định `generated` vẫn dành cho ứng dụng hiện tại.

## Cách đo

Đã khóa [8 câu mới](holdout.jsonl), [rubric](rubric.md) và các thẻ nguồn trước khi sửa. Cùng runner với các vòng trước, gồm agent thật, Qwen 1,5B gốc, 18 thẻ nguồn tiếng Việt hoặc Anh và truy xuất E5/BM25/RRF local. Đo từ lúc gọi agent đến final, ngoài thời gian nạp model. Qwen chỉ sinh ở nhánh đối chứng. Trường `docs` trong bản ghi chỉ phản ánh ngữ cảnh của lượt sinh. Chế độ trích đoạn được chấm từ các sự kiện `citation` đã phát. Assistant chấm hai nhánh theo cùng đáp án. Sáu câu có đủ nguồn thuộc các nhóm nghiệp vụ đã dùng ở pilot trước.

| Chỉ số | Tổng hợp hiện tại | Trích đoạn |
| --- | ---: | ---: |
| Có đủ hai đoạn kỳ vọng trong đầu ra | 6/6 | 6/6 |
| Trả lời trực tiếp, đúng và đủ theo rubric | 1/6 | 1/6 |
| Lỗi nghiệp vụ trọng yếu trong đầu ra | 1/6 | 0/6 |
| Hai ca thiếu nguồn được xử lý đầy đủ | 2/2 | 2/2 |
| P50 trên 6 câu đủ nguồn | 8,06 giây | 13 ms |

P02 đạt ở cả hai nhánh vì đoạn đã nêu rõ phải loại số dư nội bộ trên báo cáo hợp nhất. Nhánh tổng hợp trong P06 gán nhầm lựa chọn giá trị hợp lý cho VAS 05. Nhánh trích đoạn giữ đúng cơ sở nguyên giá và hao mòn. Trong P04, đoạn nêu đúng quy tắc giá trị thấp hơn và hai khoản mục IFRS nhưng chưa tính số tiền 690. P01 cũng thiếu lựa chọn cụ thể 25.200. Hai ca này cho thấy khoảng cách giữa một đoạn tham chiếu hữu ích và lời giải hoàn chỉnh.

[Bản tổng hợp](baseline.json) · [Bản trích đoạn](evidence.json) · [Điểm từng câu](grades.json)

## Quyết định

Giữ chế độ trích đoạn ở dạng opt-in cho việc đối chiếu nguồn. Phép thử cho thấy giá trị của nó như một chế độ xem tài liệu, còn chất lượng tổng hợp nghiệp vụ chưa đạt mức cần thiết để đưa lên staging. P50 chỉ áp dụng cho chỉ mục 18 thẻ chạy trong tiến trình, chưa đo Qdrant/TEI triển khai hoặc chấm độc lập.

Khởi động backend với `COMPARE_MODE=evidence` để thử local. Đặt lại `COMPARE_MODE=generated` để quay về chế độ tổng hợp hiện có.
