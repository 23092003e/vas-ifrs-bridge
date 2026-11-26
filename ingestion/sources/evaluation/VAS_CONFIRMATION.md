# Xác nhận pipeline QA VAS

So sánh cả pipeline TEI hiện tại với RRF top 8 giới hạn 3.000 token nội dung nguồn. Giữ cùng model Qwen 14B, chỉ mục VAS, prompt ứng dụng và trần sinh 160 token của benchmark local. Thay đổi gộp cả rerank và cách đóng gói context, nên phép đo chỉ đánh giá chênh lệch đầu cuối của hai cấu hình.

## Bộ câu hỏi và rubric

[Bộ 24 câu](vas-confirmation-v1.jsonl) gồm sáu câu mỗi nhóm tra cứu trực tiếp, nhiều điều kiện, ngoại lệ và thiếu dữ liệu. Mỗi câu có nội dung đáp án bắt buộc, mã đoạn nguồn và dấu hiệu văn bản. Đã xác thực 37 dấu hiệu trong ba tệp nguồn và kiểm tra câu hỏi không trùng nguyên văn với các bộ trước. [Tệp khóa](vas-confirmation-v1.lock.json) ghi SHA-256 của bộ câu và các tệp nguồn. Bộ nhãn do assistant soạn và đối chiếu. Chưa có người có chuyên môn độc lập rà soát trước khi chạy.

- **Đúng** khi câu trả lời có đủ ý bắt buộc và không đưa ra kết luận mâu thuẫn. Với câu thiếu dữ liệu, yêu cầu nêu đúng dữ kiện còn thiếu và tránh tự đưa ra số hoặc quyết định.
- **Đúng có trích dẫn hỗ trợ** khi các đoạn mà API thực sự trích dẫn đủ để hỗ trợ các kết luận bắt buộc. Kiểm tra nội dung đoạn được trích, thay vì chỉ đếm khóa `[Cn]` hay từ khóa trùng.
- **Lỗi nghiêm trọng** khi câu trả lời đề xuất cách ghi nhận, đo lường hay trình bày sai có thể thay đổi kết quả kế toán, hoặc tự điền số hay kết luận khi thiếu dữ liệu. Lỗi diễn đạt và lời giải bị cắt không tự động được xếp nghiêm trọng.

## Phép đo và tiêu chí chốt

Mỗi câu gửi thành hai request riêng qua HTTP SSE và luân phiên thứ tự hai nhánh. Kiểm tra nội dung `final` đã lưu bằng API hội thoại. Nhánh TEI dùng toàn bộ ứng viên của ứng dụng và timeout 15 giây. Nhánh RRF dùng thứ hạng dự phòng của ứng dụng ngay lập tức rồi giới hạn context. Ghi riêng `scored`, `timeout` và các lý do dự phòng khác. Độ trễ tổng tính từ khi bắt đầu request đến khi luồng SSE đóng. p95 dùng thứ hạng gần nhất trên tất cả 24 lượt mỗi nhánh, có tính cả lượt TEI chạy dự phòng.

Chỉ đề xuất đổi mặc định nếu nhánh RRF đúng thêm ít nhất ba câu, giữ số câu đúng có trích dẫn hỗ trợ, không có lỗi nghiêm trọng mới trên cùng câu và p95 tăng không quá 20%. Cả hai nhánh phải hoàn tất SSE, TEI phải trả đủ điểm cho ít nhất 13/24 lượt và cần chấm độc lập trên nhãn đã xác minh trước khi chạy. Thiếu các điều kiện này thì giữ kết quả ở mức thử nghiệm local.

## Kết quả

| Chỉ số | Pipeline hiện tại | RRF giới hạn 3.000 token |
| --- | ---: | ---: |
| SSE hoàn tất và lưu phản hồi | 24/24 | 24/24 |
| Đúng đủ ý | 4/24 | 15/24 |
| Đúng có trích dẫn hỗ trợ | 0/24 | 7/24 |
| Câu có lỗi nghiêm trọng | 9/24 | 5/24 |
| Độ trễ p50 | 68,18 s | 54,27 s |
| Độ trễ p95 | 75,78 s | 70,21 s |
| TEI trả điểm | 0/24 | Bỏ qua theo cấu hình |

Trong bốn nhóm theo thứ tự tra cứu trực tiếp, nhiều điều kiện, ngoại lệ và thiếu dữ liệu, số câu đúng thay đổi lần lượt từ 3 lên 6, 0 lên 2, 1 lên 4 và 0 lên 3. Cả 24 lượt baseline đều gửi 40 ứng viên tới TEI và chạm timeout, sau đó chạy thứ hạng dự phòng. Vì vậy chênh lệch chất lượng và độ trễ chỉ phản ánh đối chiếu với **pipeline local đang chạy dự phòng**. Phép đo chưa xác định chênh lệch so với TEI trả điểm thành công.

Mặc dù tổng số lỗi nghiêm trọng giảm, nhánh RRF có năm lỗi nghiêm trọng mới ở các câu 07, 08, 13, 14 và 21. Ví dụ, nhánh này gọi máy mua trả chậm là tài sản cố định vô hình và đảo điều kiện giảm giá nguyên liệu ngay trong phần kết luận. Câu 07 có một điểm mơ hồ về giá niêm yết đã gồm thuế hay chưa. Giữ nguyên đáp án khóa và kiểm tra độ nhạy bằng cách chấp nhận kết quả của nhánh hiện tại theo cách đọc giá đã gồm thuế. Điểm khi đó là 5/24 so với 15/24 và quyết định giữ nguyên.

**Giữ cấu hình hiện tại trong ứng dụng.** Nhánh RRF đạt tiêu chí chênh lệch số câu đúng, trích dẫn có hỗ trợ và p95, nhưng chưa đạt tiêu chí không có lỗi nghiêm trọng mới. TEI không trả điểm ở lượt nào và phép chấm hiện tại do assistant thực hiện với tên nhánh được ẩn. Chưa có xác nhận nghiệp vụ độc lập.

[Bản ghi 48 lượt SSE](vas-confirmation-v1.results.json) · [Tổng hợp và điểm từng câu](vas-confirmation-v1.summary.json) · [Phiếu chấm ẩn tên cấu hình](vas-confirmation-v1.review.jsonl) · [Điểm nội bộ theo phiếu](vas-confirmation-v1.internal-grades.json)

## Chạy và chấm lại

Dùng môi trường loopback trong [báo cáo FastAPI SSE](VAS_API_BENCHMARK.md), rồi chạy các lệnh dưới đây. Phiếu chấm dùng `X` và `Y` được đảo theo từng câu, ẩn tên cấu hình, thời gian và trạng thái TEI.

```sh
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_api_eval.py \
  --confirmation --max-tokens 160 \
  --out ingestion/sources/evaluation/vas-confirmation-v1.results.json

apps/backend/.venv/bin/python ingestion/sources/evaluation/score_vas_confirmation.py \
  --results ingestion/sources/evaluation/vas-confirmation-v1.results.json \
  --out ingestion/sources/evaluation/vas-confirmation-v1.review.jsonl
```

Tệp điểm đầu vào có `reviewer`, `independent_reviewer`, `labels_verified_before_run` và `grades`. `grades` ánh xạ ID câu đến hai mục `X` và `Y`, mỗi mục chứa `correct`, `supported`, `serious` và `reason`. Chạy lại lệnh chấm với `--grades` và đường dẫn tệp này để xuất điểm đã giải mã và kết quả từng tiêu chí.
