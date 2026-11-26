# Kiểm tra prompt nêu kết luận trước

[Phép đo context trước đó](VAS_RRF_CONTEXT_BUDGET.md) chỉ ra hai chỗ thông tin bị mất. Một prompt toàn văn bị Ollama cắt từ 4.337 xuống 2.050 token, nên số dấu hiệu trong văn bản chuẩn bị trước khi gửi có thể cao hơn số model nhận được. Khi prompt đã vừa cửa sổ model, một số câu vẫn dừng giữa danh sách điều kiện trước khi trả lời câu hỏi. Ví dụ, câu doanh thu đã liệt kê đủ năm điều kiện nhưng thiếu kết luận về việc ghi nhận trong tình huống được hỏi.

Thử đúng một bản sửa prompt. Thay đoạn yêu cầu phân tích tuần tự bằng yêu cầu mở đầu bằng kết luận ngắn, sau đó nêu các điều kiện hoặc ngoại lệ liên quan và trích dẫn. Giữ yêu cầu dựa trên nguồn và phân biệt ghi nhận ban đầu với đo lường sau ghi nhận khi cần. Hai nhánh giữ cùng Qwen 14B, trần 160 token sinh, top 8 RRF, tối đa 3.000 token nội dung nguồn và cùng thứ tự chunk. Chạy xen kẽ thứ tự hai nhánh qua FastAPI SSE.

Phép đo chọn năm câu dev trước khi chạy. Doanh thu và Thông tư 99 từng dừng trước kết luận đầy đủ. Dự phòng và sự kiện không điều chỉnh là ca đối chứng giữ độ đúng. Ca thiếu dữ liệu kiểm tra tiếp tục từ chối tính số tiền. Chấm theo các ý bắt buộc của benchmark trước và ẩn nhãn cấu hình khi xem câu trả lời. Chỉ cân nhắc áp dụng nếu số câu đúng tăng, hoặc số câu đúng có đủ dấu hiệu trong đoạn được trích tăng mà số câu đúng không giảm. Không chấp nhận lỗi nghiệp vụ mới.

## Kết quả

| Prompt | Đúng đủ ý | Đúng và đủ dấu hiệu trong đoạn được trích | Câu phát citation | Tổng p50 | TTFT p50 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Phân tích tuần tự | 2/5 | 1/5 | 2/5 | 38,50 s | 20,26 s |
| Nêu kết luận trước | 2/5 | 0/5 | 5/5 | 35,79 s | 26,88 s |

Cả 10 lượt trả lời và lưu được phản hồi. Từng cặp dùng đúng cùng văn bản context. Prompt mới trả lời đúng câu doanh thu và từ chối tính khi thiếu dữ liệu. Nó bỏ ngưỡng giá trị thuần thấp hơn giá gốc ở câu dự phòng, bỏ ý giữ nguyên số liệu ở câu sự kiện sau kỳ và diễn giải sai phạm vi ngoại lệ của Thông tư 99. Tổng số câu đúng không tăng và số câu đúng có đủ dấu hiệu trong đoạn được trích giảm. Giữ prompt hiện tại trong ứng dụng. Đây là phép thử trên năm câu dev, chấm nội bộ và mỗi cấu hình sinh một lần cho mỗi câu.

[Bản ghi SSE](vas-api-conclusion-first-v1.json) · [Điểm từng câu](vas-api-conclusion-first-v1.grades.json)

## Chạy lại

Dùng cùng cấu hình stack tại [benchmark FastAPI SSE](VAS_API_BENCHMARK.md).

```sh
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_api_eval.py \
  --rrf-only --bounded-rrf --conclusion-first --max-tokens 160 \
  --out ingestion/sources/evaluation/vas-api-conclusion-first-v1.json
```
