# Compare trên 24 câu tự do

Đợt này đánh giá chất lượng diễn giải và trích dẫn của Compare hiện tại. Tập gồm 20 câu đối chiếu có thể trả lời với hai nguồn và 4 tình huống có chuẩn mực bị thiếu. Có 12 câu tiếng Việt và 12 câu tiếng Anh. Các câu đặt tình huống mới trên sáu nhóm nghiệp vụ của bộ thẻ hiện có. Các nhóm lặp lại cùng quy tắc kế toán nên 24 câu thể hiện nhiều cách hỏi, với độ phủ nghiệp vụ giới hạn.

Đã khóa [câu hỏi](holdout.jsonl), [quy tắc chấm](rubric.md) và corpus trước lần chạy. [Mã băm đầu vào](inputs.sha256) và [mã băm ca chạy](runtime.sha256) dùng để kiểm tra phiên bản. Assistant soạn câu hỏi và chấm theo thẻ nên kết quả chưa có rà soát độc lập.

Agent Compare dùng Qwen2.5-1.5B-Instruct gốc float32 trên Apple Metal. Giới hạn là 170 token, mỗi câu sinh một lần. Runner gọi agent thật và thay tích hợp Qdrant/TEI bằng truy xuất cục bộ trên 18 thẻ, với E5, BM25 và RRF. Độ trễ là thời gian từ lúc gọi agent đến sự kiện final. Dùng để đọc hiệu năng lượt local này. Kết quả của tập cũ có kích thước và câu hỏi khác.

## Tái lập

Từ thư mục gốc, đặt `HF_HOME` trỏ đến cache checkpoint khóa trong runner.

```bash
export HF_HUB_OFFLINE=1 PYTORCH_ENABLE_MPS_FALLBACK=1 PYTHONPATH=apps/backend
export VAS_COMPARE_EVAL=ingestion/sources/evaluation/compare-v3
shasum -c "$VAS_COMPARE_EVAL/inputs.sha256"
shasum -c "$VAS_COMPARE_EVAL/runtime.sha256"
apps/backend/.venv/bin/python ingestion/sources/evaluation/compare-v2/run.py /private/tmp/vas-compare-v3.json --questions "$VAS_COMPARE_EVAL/holdout.jsonl"
```

## Kết quả

| Chỉ số | Kết quả |
| --- | ---: |
| Có đủ hai nguồn trong ngữ cảnh | 20/20 |
| Có trích dẫn đủ hai đoạn kỳ vọng | 14/20 |
| Đúng nghiệp vụ, đủ ý và dẫn đủ nguồn | 4/20 |
| Sai nghiệp vụ trọng yếu trong bản final | 5/20 |
| Trả lời thiếu ý trọng yếu | 6/20 |
| Từ chối dù đủ nguồn | 5/20 |
| Kiềm chế kết luận về chuẩn bị thiếu nguồn | 4/4 |
| Đạt yêu cầu đầy đủ ở nhóm thiếu nguồn | 3/4 |
| Độ trễ p50 của 20 câu hai phía | 7,59 giây |

Cả năm câu sai trọng yếu vẫn dẫn đủ hai mã đoạn. E01 ghi giao dịch chuyển nợ thành vốn chủ sở hữu vào dòng tiền tài chính dù đoạn IAS 7 nói loại khỏi báo cáo lưu chuyển tiền tệ. E08 giữ doanh thu và số dư nội bộ ở phía VAS dù đoạn dẫn nói loại trừ. E13 và E14 nhầm tỷ lệ quyền biểu quyết hoặc ảnh hưởng đáng kể với quyền kiểm soát. Bốn câu đạt gồm ba câu tỷ giá và một câu loại trừ số dư nội bộ. Ở nhóm thiếu nguồn, E23 báo thiếu VAS 20 đúng nhưng bỏ phần IAS 40 vì model gắn nhận định đó dưới nhãn VAS.

## Quyết định

Giữ thay đổi phân luồng nguồn và kiểm tra mã để kiểm thử tiếp. Kết quả chưa đạt tiêu chí thử staging đã ghi trước. Trên bộ thẻ này, ưu tiên kiểm tra từng nhận định xem đoạn được dẫn hỗ trợ, mâu thuẫn hay thiếu dữ kiện. Thiết kế phép đối chứng tạo nhận định theo từng đoạn rồi tổng hợp sau kiểm tra. Lượt này chưa cung cấp cơ sở để chọn một đợt fine-tuning tiếp theo.

[Bản ghi từng câu](results.json) · [Điểm và lý do chấm](grades.json)
