# Kiểm tra ý nghĩa trích dẫn của Compare

Thử bộ kiểm tra offline trên các đoạn Compare đã xuất. Đối chứng và nhánh kiểm tra dùng cùng câu hỏi, nguồn, Qwen2.5-1.5B-Instruct gốc và chính xác cùng một bản sinh. Bộ kiểm tra dùng một lượt phân loại riêng bằng cùng checkpoint, với prompt dành cho xác minh. Đầu vào là câu hỏi, toàn bộ nhận định trong một đoạn và đúng các đoạn mà nó dẫn. So điểm ba nhãn ở token trả lời đầu tiên. Chỉ giữ đoạn có nhãn **được hỗ trợ**, loại đoạn **mâu thuẫn** hoặc **thiếu bằng chứng** và cập nhật danh sách trích dẫn tương ứng. Cảnh báo thiếu nguồn được giữ.

Giai đoạn chẩn đoán dùng [15 nhận định đã gán nhãn](controls.json) từ Compare v3. Giai đoạn chính dùng [16 câu mới](holdout.jsonl) trên bộ 18 thẻ hiện có, mỗi câu sinh một lần. [Rubric và tiêu chí staging](rubric.md) đã được khóa cùng dữ liệu trước khi chạy. Assistant soạn và chấm câu theo nguồn, chưa có người rà soát độc lập. Tập mới đặt các tình huống khác nhưng lặp lại sáu nhóm nghiệp vụ của Compare v3.

Đây là phép thử local với Apple Metal, float32, Qwen 1,5B và truy xuất E5/BM25/RRF trên thẻ. Không chỉnh agent hoặc prompt đang phục vụ. Độ trễ nhánh thử là thời gian baseline cộng thời gian xác minh từng đoạn của cùng câu. Thời gian nạp checkpoint nằm ngoài phép đo. Đây là ước lượng tuần tự offline của chi phí bổ sung.

## Tái lập

Đặt `HF_HOME` trỏ tới cache checkpoint đã khóa. Thực hiện từ thư mục gốc.

```bash
export HF_HUB_OFFLINE=1 PYTORCH_ENABLE_MPS_FALLBACK=1 PYTHONPATH=apps/backend
export VAS_COMPARE_VERIFY=ingestion/sources/evaluation/compare-v4
shasum -c "$VAS_COMPARE_VERIFY/inputs.sha256"
shasum -c "$VAS_COMPARE_VERIFY/runtime.sha256"
apps/backend/.venv/bin/python "$VAS_COMPARE_VERIFY/verify_claims.py" controls "$VAS_COMPARE_VERIFY/control-results.json"
apps/backend/.venv/bin/python ingestion/sources/evaluation/compare-v2/run.py "$VAS_COMPARE_VERIFY/baseline.json" --questions "$VAS_COMPARE_VERIFY/holdout.jsonl"
apps/backend/.venv/bin/python "$VAS_COMPARE_VERIFY/verify_claims.py" holdout "$VAS_COMPARE_VERIFY/verified.json"
```

## 1. Chẩn đoán

Bộ kiểm tra loại 2/5 nhận định lỗi và giữ 5/10 nhận định đúng. Nó phát hiện hai nhận định đưa giao dịch phi tiền tệ vào báo cáo lưu chuyển tiền tệ. Ba lỗi lọt qua là giữ doanh thu nội bộ khi hợp nhất và hai nhận định nhầm ảnh hưởng đáng kể với quyền kiểm soát. Các nhận định đúng bị loại thuộc các câu tỷ giá. Kết quả này làm rõ hai rủi ro đối nghịch của bộ kiểm tra trước khi đọc tập chính. [Kết quả từng nhãn](control-results.json)

## 2. Đối chứng trên 16 câu mới

Cả 12 câu đối chiếu đều có đủ nguồn kỳ vọng trong ngữ cảnh ban đầu. Hai nhánh chỉ khác ở bước lọc nhận định. Chấm kết luận theo cùng đáp án và rubric.

| Chỉ số | Compare hiện tại | Thêm kiểm tra offline |
| --- | ---: | ---: |
| Sai nghiệp vụ trọng yếu lọt qua | 2/12 | 1/12 |
| Đúng, đủ ý và đủ nguồn | 3/12 | 2/12 |
| Trích dẫn đủ hai đoạn kỳ vọng | 8/12 | 5/12 |
| Từ chối toàn bộ dù có đủ nguồn | 2/12 | 3/12 |
| Xử lý an toàn khi thiếu nguồn | 4/4 | 4/4 |
| Đạt đầy đủ ở nhóm thiếu nguồn | 2/4 | 2/4 |
| P50 trên 12 câu đối chiếu | 7,75 giây | 8,82 giây |

V01 là lỗi được chặn. Bản hiện tại ghi nhận phát hành cổ phần phi tiền tệ vào báo cáo lưu chuyển tiền tệ, còn bản thử từ chối toàn bộ. V04 cho thấy mất câu trả lời hữu ích. Bộ kiểm tra xóa cả hai nhận định IAS 21 vừa đúng vừa có nguồn, làm câu chỉ còn phía VAS. V12 cho thấy rủi ro còn lại. Bộ kiểm tra giữ hai nhận định sai về ghi nhận thuê hoạt động theo VAS và điều kiện 12 tháng theo IFRS.

[Bản sinh đối chứng](baseline.json) · [Nhận định và kết quả kiểm tra](verified.json) · [Điểm và lý do từng câu](grades.json)

## 3. Quyết định staging

Không đạt tiêu chí đã khóa. Còn lỗi nghiệp vụ trọng yếu, số câu đạt giảm từ 3 xuống 2 và tỷ lệ đạt dưới mức đa số. Giữ bộ kiểm tra trong thư mục đánh giá và để nguyên ứng dụng phục vụ. Nếu thử phương án tiếp theo, phép đối chứng nên giữ riêng cách viết nhận định và kiểm tra bằng chứng để xác định phần nào làm mất kết luận đúng. Lượt này chưa dùng Qdrant/TEI triển khai hoặc người chấm độc lập.
