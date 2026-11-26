# Benchmark VAS qua FastAPI SSE

Đo qua HTTP `POST /v1/chat/stream` của ứng dụng thật. Runner kiểm tra luồng SSE, nội dung trả lời cuối cùng và đọc lại hội thoại qua `GET /v1/chat/conversations/{id}`. Cả hai cấu hình dùng cùng Qwen2.5 14B Instruct Q4_K_M trên Ollama 0.32.0, cùng prompt hệ thống, dữ liệu, câu hỏi và trần 160 token đầu ra. Câu hỏi chạy theo cặp, luân phiên cấu hình nào đi trước. Phạm vi là QA tiếng Việt trên dữ liệu dùng chung, với tài khoản kiểm thử local (`DEV_AUTH_BYPASS=true`).

## Dữ liệu và cấu hình

- Qdrant 1.18.2 local chứa 359 chunk trong `kb_shared_vas` từ Quyết định 149/2001, 100/2005, 12/2005 và phần 1 Thông tư 99/2025. Runner xác thực checksum theo [manifest nguồn](../downloads.json). Các collection IFRS, mapping và guidance để trống. Đây là chỉ mục mới; phạm vi khác chỉ mục VM cũ và nhỏ hơn bộ VAS đã thu thập.
- Retriever backend dùng dense `bge-m3` qua Ollama, sparse BM25 và hợp nhất kết quả của ứng dụng. TEI CPU 1.5 chạy [bge-reranker-v2-m3 ONNX](https://huggingface.co/onnx-community/bge-reranker-v2-m3-ONNX/tree/6f5ff65298512715a1e669753bc754d2bc8f367b) trong container amd64 trên máy ARM64. Graph đóng gói có 124 nút, 178 cạnh và chỉ hai mã chuẩn mực trên các nút có `standard_code`, `IFRS-1` và `IFRS-2`. Không mã nào do ontology suy ra từ 13 câu đánh giá giao với hai mã đó. Vì vậy các lượt QA này không đo được giá trị của việc bổ sung đoạn nguồn từ graph. Runner đếm riêng số lần QA gọi tìm mục liên quan.
- Trong cả hai nhánh so sánh, TEI chấm tối đa 8 ứng viên hợp nhất đầu tiên, mỗi ứng viên tối đa 96 từ, với timeout 60 giây dành riêng cho benchmark. Ứng viên ngoài nhóm này không thể vượt ngưỡng điểm của reranker. Lượt smoke giữ mặc định ứng dụng là tối đa 40 ứng viên và timeout 15 giây.
- **Toàn văn** giữ cơ chế đóng gói context của workspace, gồm sửa lỗi đưa toàn văn vào prompt. **Chọn đoạn** xếp hạng các đoạn theo BM25, giới hạn phần nội dung nguồn ở 512 token. Khi câu hỏi có tín hiệu nhiều vế như “và”, “điều kiện”, “ngoại lệ”, runner dùng cửa sổ rộng hơn và trần 1.024 token. Cả hai giữ citation key của chunk nguồn. Mọi thay đổi thử nghiệm nằm trong runner.
- Tập dev có 7 câu từ pilot. [Holdout mới](vas-api-new-v1.jsonl) có 6 câu chưa xuất hiện trong các lượt đo trước, cùng 11 dấu hiệu đã đối chiếu với đoạn nguồn. [Tệp khóa](vas-api-new-v1.lock.json) ghi SHA-256 của bộ câu hỏi và hai văn bản được dùng cho nhãn. Đây là holdout ở cấp câu hỏi, có dùng lại một số chuẩn mực và văn bản của dev.

## Smoke với rerank mặc định

Luồng SSE sinh câu trả lời và lưu thành công. TEI chạm timeout sau khoảng 15,01 giây khi nhận 40 ứng viên. Backend chuyển sang thứ hạng dự phòng và lấy 8 chunk. Context dựng trước khi gửi model dài 4.174 token. Token đầu đến sau 42,78 giây và SSE kết thúc sau 83,63 giây. Chỉ đo một câu. [Bản ghi smoke](vas-api-smoke-v1.json)

## Cách đọc số đo

Điểm nghiệp vụ yêu cầu đủ ý bắt buộc và không có lỗi nghiệp vụ làm thay đổi kết luận. Khi câu hỏi yêu cầu một số tiền hoặc quyết định ghi nhận, câu trả lời cần nêu kết luận trực tiếp. Assistant chấm nội dung từng cặp với nhãn cấu hình được ẩn. Dấu hiệu chỉ kiểm tra chuỗi trong context trước khi gửi model và trong các chunk có citation được trả về. Ollama dùng cửa sổ context 4.096 token ở lượt local này, nên số chuỗi tìm được trước khi gửi có thể cao hơn số model thực sự thấy. Dấu hiệu chỉ là phép kiểm tra độ phủ văn bản, chưa xác nhận mọi nhận định trong câu trả lời được citation hỗ trợ. TTFT tính từ lúc bắt đầu gửi HTTP đến token SSE đầu tiên. Độ trễ tổng kết thúc khi luồng SSE đóng, trước lượt GET để kiểm tra dữ liệu lưu. Hai chỉ số bao gồm thời gian truy xuất, TEI và sinh văn bản; thông số máy thử quyết định nhiều về số giây tuyệt đối.

## Kết quả dev

| Context | Đúng nghiệp vụ | Đúng và đủ dấu hiệu trong đoạn trích dẫn | Dấu hiệu trong prompt | Dấu hiệu trong đoạn trích dẫn | Context p50 | TTFT p50 | Tổng p50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Toàn văn | 3/7 | 1/7 | 6/14 | 5/14 | 1.537 token | 34,62 s | 60,65 s |
| Chọn đoạn | 2/7 | 0/7 | 3/14 | 2/14 | 919 token | 27,94 s | 54,09 s |

Tất cả 14 lượt hoàn thành, có điểm TEI và lưu đúng nội dung qua API. Thứ tự chunk trước khi chọn đoạn giống nhau trong cả bảy cặp. Mỗi cấu hình phát SSE citation ở 4/7 câu. Trong câu trả lời cuối không còn khóa citation chưa phân giải, sau khi đã qua hậu xử lý của ứng dụng. Bộ chọn dùng trần mở rộng ở 6/7 câu. Các lỗi chính gồm câu trả lời dừng trước kết luận, gán sai chuẩn mực và bỏ phạm vi ngoại lệ của Thông tư 99.

[Bản ghi dev](vas-api-dev-v1.json) · [Điểm từng câu](vas-api-dev-v1.grades.json)

## Kết quả holdout mới

| Context | Đúng nghiệp vụ | Đúng và đủ dấu hiệu trong đoạn trích dẫn | Dấu hiệu trong prompt | Dấu hiệu trong đoạn trích dẫn | Context p50 | TTFT p50 | Tổng p50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Toàn văn | 4/6 | 2/6 | 10/11 | 5/11 | 2.590 token | 44,57 s | 65,52 s |
| Chọn đoạn | 4/6 | 3/6 | 8/11 | 6/11 | 975 token | 26,11 s | 41,98 s |

Cả 12 lượt holdout có điểm TEI và lưu được phản hồi. Thứ tự chunk trước khi chọn đoạn trùng trong cả sáu cặp. Bộ chọn dùng trần mở rộng ở 5/6 câu, nên kết quả chủ yếu phản ánh chế độ mở rộng. Chọn đoạn giảm 62% context trung vị và 36% độ trễ tổng trung vị. Tính theo từng cặp, độ trễ tổng giảm trung vị 16,81 giây. Hai cấu hình đúng cùng số câu nhưng khác ca. Chọn đoạn kết luận kịp ở câu TSCĐ, còn toàn văn nêu chính xác nơi thuyết minh cổ tức. Mỗi câu holdout có ít nhất một chunk trong chỉ mục chứa đủ dấu hiệu. Ở ca chiết khấu, kết quả sau rerank của cả hai thiếu dấu hiệu chiết khấu thương mại. Ở ca cổ tức, toàn văn có cả hai dấu hiệu và bộ chọn bỏ cả hai.

[Bản ghi holdout](vas-api-new-v1.results.json) · [Điểm từng câu](vas-api-new-v1.grades.json)

## Kết luận

Giữ toàn văn trong đường chạy ứng dụng. Bộ chọn giảm độ trễ trên holdout nhưng làm mất bằng chứng nguồn và giảm điểm nghiệp vụ trên dev. Trên holdout, tổng điểm nghiệp vụ giữ nguyên, đồng thời có câu mất bằng chứng và có câu trích dẫn tốt hơn. Với 13 câu và một lần sinh mỗi cấu hình, kết quả chỉ đủ để giữ bộ chọn làm ứng viên thử nghiệm. Graph không tham gia mở rộng ở các lượt đo, nên chưa có điểm đóng góp riêng cho graph.

Đối chứng model độc lập đã có trong [benchmark Qwen 14B trước đó](VAS_QWEN14B.md). Cùng checkpoint trên sáu câu khác, RAG toàn văn đạt 5/6 và model độc lập đạt 3/6. Phép đối chứng đó dùng E5, BM25 SQLite và Qdrant nhúng, nên số tăng hai câu đúng chỉ quy cho RAG của thí nghiệm đó. Hai nhánh SSE hiện tại dùng cùng trọng số. Chất lượng fine-tuning chưa được đo vì chưa có checkpoint và tập train/test phù hợp. Chưa có chấm nghiệp vụ độc lập, thử nghiệm IFRS hay luồng Next.js với đăng nhập thật trong lượt này.

## Chạy lại

Các dịch vụ dùng cổng loopback riêng. Postgres ở `15432`, Redis ở `16379`, Qdrant ở `16333`, Ollama ở `11436` và TEI ở `18080`. FastAPI của runner tự mở cổng `18081`. Dùng database thử nghiệm đã chạy các migration, Qdrant trống để seed và cache tokenizer tương ứng với revision trong runner.

```sh
export APP_ENV=test DEV_AUTH_BYPASS=true QDRANT_API_KEY=''
export DATABASE_URL=postgresql+asyncpg://vas_eval:vas_eval@127.0.0.1:15432/vas_eval
export QDRANT_URL=http://127.0.0.1:16333 OLLAMA_BASE_URL=http://127.0.0.1:11436
export REDIS_URL=redis://127.0.0.1:16379/0 TEI_URL=http://127.0.0.1:18080
export HF_HOME=/private/tmp/vas-benchmark-hf PYTHONPATH=apps/backend

apps/backend/.venv/bin/python ingestion/sources/evaluation/seed_vas_api_eval.py
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_api_eval.py \
  --rerank-limit 8 --max-tokens 160 --out ingestion/sources/evaluation/vas-api-dev-v1.json
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_api_eval.py \
  --rerank-limit 8 --max-tokens 160 --new \
  --out ingestion/sources/evaluation/vas-api-new-v1.results.json
```

Digest Ollama của `qwen2.5:14b-instruct` là `7cdf5a0187d5c58cc5d369b255592f7841d1c4696d45a8c8a9489440385b22f6`. Digest của `bge-m3` là `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab`. Test backend chạy với `python -m pytest tests/unit -q` từ `apps/backend` qua môi trường `.venv`. Cả 121 test qua.
