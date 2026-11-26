# Giới hạn context cho RRF qua FastAPI SSE

Tiếp nối [đo riêng reranker](VAS_RERANK_BENCHMARK.md), trong đó RRF giữ nhiều dấu hiệu bằng chứng hơn TEI trên dev, nhưng sáu prompt vượt 4.096 token và chưa cải thiện số câu đúng. Thí nghiệm này giữ RRF ở cả hai nhánh để đo riêng cách đóng gói context.

## Thiết kế

- Bảy câu dev VAS, mỗi câu hai lượt HTTP SSE. Cả hai dùng Qwen 14B qua Ollama, cùng prompt, giới hạn 160 token sinh, tài khoản kiểm thử local và top 8 của Qdrant RRF. Runner luân phiên thứ tự hai nhánh. Lượt thứ hai dùng lại đúng ứng viên và thứ tự từ lượt đầu, đồng thời ghi riêng liệu truy xuất trực tiếp ở lượt đó có trùng hay không.
- Nhánh toàn văn gửi toàn bộ chunk lấy được. Nhánh có giới hạn dành tối đa 3.000 token cho nội dung nguồn. Hai chunk đầu được giữ nguyên trong giới hạn 850 token mỗi chunk. Các chunk sau có tối đa 350 token mỗi chunk và chia đều ngân sách còn lại. Nội dung quá dài lấy cửa sổ khớp từ khóa với câu hỏi bằng bộ chọn BM25 đã có. Khi không có cửa sổ vừa ngân sách, giữ prefix trong giới hạn. Chunk giữ thứ tự và citation key như nhánh toàn văn.
- Chọn cách đóng gói bằng cách thử lại trên các chunk đã lưu của dev. Dấu hiệu và đáp án dùng để chấm kết quả. Bộ chọn chỉ nhận văn bản chunk, câu hỏi và ngân sách. Hai nhánh dùng mã ontology đã được ổn định thứ tự ở lượt trước. Các thay đổi trong thí nghiệm chỉ nằm ở runner.
- Đo TTFT và thời gian kể từ HTTP request đến khi SSE đóng. Dùng tokenizer họ Qwen2.5 đã khóa của benchmark để đếm văn bản dựng trước khi gửi. Ollama dùng cửa sổ 4.096 token ở stack này. Tính độ phủ bằng dấu hiệu văn bản đã gán nhãn và chấm câu trả lời theo đủ các ý bắt buộc. Chỉ tính các citation thực sự được API phát.

Log runtime xác nhận có lượt toàn văn bị cắt ngay tại Ollama. Ở một lượt, Ollama ghi `prompt=4337`, `limit=2050`, `new=2050`. Cũng trong phép đo này, một lượt prompt ngắn đi vào slot với `task.n_tokens=3100`. Vì vậy phân tích báo riêng dấu hiệu trước khi gửi, câu trả lời đã sinh và citation từ SSE. Độ phủ trước khi gửi có thể cao hơn những gì model thực sự nhận được.

## Kết quả dev

| Context RRF | Câu đúng | Dấu hiệu trước khi gửi | Dấu hiệu trong đoạn được trích | Câu phát citation | Context p50 | TTFT p50 | Tổng p50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Toàn văn | 2/7 | 12/14 | 0/14 | 0/7 | 4.093 token | 24,13 s | 52,72 s |
| Giới hạn 3.000 token nội dung nguồn | 5/7 | 11/14 | 4/14 | 3/7 | 2.828 token | 29,83 s | 61,63 s |

Tất cả 14 lượt đều phát câu trả lời và lưu được bằng Postgres. Hai lượt của mỗi cặp có danh sách chunk truy xuất trực tiếp giống nhau. Sáu prompt hệ thống toàn văn vượt 4.096 token, trong khi prompt hệ thống dài nhất của nhánh giới hạn là 3.357 token. Nhánh giới hạn tăng ba câu đúng và tốn thêm 6,71 giây ở trung vị chênh lệch theo từng cặp. Một câu trả lời đưa đúng số tiền dù thiếu dấu hiệu so khớp chính xác. Câu doanh thu có đủ dấu hiệu nhưng vẫn bị cắt trước kết luận. Câu Thông tư 99 nêu được ngày áp dụng nhưng thiếu điều kiện văn bản thay thế.

[Bản ghi dev](vas-api-rrf-budget-dev-v1.json) · [Điểm từng câu](vas-api-rrf-budget-dev-v1.grades.json)

## Kết quả trên bộ sáu câu đã khóa

| Context RRF | Câu đúng | Dấu hiệu trước khi gửi | Dấu hiệu trong đoạn được trích | Câu phát citation | Context p50 | TTFT p50 | Tổng p50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Toàn văn | 0/6 | 10/11 | 0/11 | 0/6 | 4.128 token | 18,79 s | 46,00 s |
| Giới hạn 3.000 token nội dung nguồn | 4/6 | 10/11 | 4/11 | 5/6 | 2.804 token | 31,69 s | 55,39 s |

Cả 12 lượt đều lưu được phản hồi. Một lượt truy xuất có thứ tự khác lượt trước trong cặp. Runner giữ thứ tự đã cố định cho phép so sánh. Sáu prompt hệ thống toàn văn vượt 4.096 token, trong khi prompt hệ thống dài nhất của nhánh giới hạn là 3.117 token. Trung vị chênh lệch thời gian tổng tính theo từng cặp là tăng 0,85 giây. Trên cả hai tập, đây là đối chiếu cùng câu hỏi và cùng chunk. Thời gian p50 của từng nhánh chịu ảnh hưởng của từng lượt sinh và thứ tự chạy.

Trong nhánh giới hạn, 4/6 câu đúng và có đủ dấu hiệu trong prompt. Chỉ 1/6 câu vừa đúng vừa có đủ dấu hiệu trong các đoạn đã trích. Câu chiết khấu vẫn thiếu dấu hiệu trong top 8, còn câu TSCĐ có dấu hiệu nhưng câu trả lời dừng trước quyết định ghi nhận. Phần cắt của Ollama và phần sinh câu trả lời là hai vị trí lỗi riêng.

[Bản ghi bộ sáu câu](vas-api-rrf-budget-holdout-v1.json) · [Điểm từng câu](vas-api-rrf-budget-holdout-v1.grades.json)

## Quyết định

Giữ cấu hình giới hạn 3.000 token trong runner làm ứng viên đã đo. Kết quả xác nhận lợi ích của giới hạn context khi chạy RRF top 8 trên QA VAS local. Điều kiện thay cấu hình ứng dụng vẫn cần đối chiếu cùng lượt với pipeline TEI và bộ câu mới có chấm độc lập. Bộ sáu câu hiện tại đã được sử dụng ở các benchmark trước và chưa có chấm độc lập. Tác động với nhiều lượt hội thoại, IFRS và fine-tuning chưa được đo ở đây.

## Chạy lại

Dùng các biến môi trường, database và chỉ mục local ở [benchmark FastAPI SSE](VAS_API_BENCHMARK.md).

```sh
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_api_eval.py \
  --rrf-only --bounded-rrf --max-tokens 160 \
  --out ingestion/sources/evaluation/vas-api-rrf-budget-dev-v1.json
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_api_eval.py \
  --rrf-only --bounded-rrf --max-tokens 160 --new \
  --out ingestion/sources/evaluation/vas-api-rrf-budget-holdout-v1.json
```
