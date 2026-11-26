# Qwen 14B local cho VAS

## Oracle trên tập dev

Chạy tag `qwen2.5:14b-instruct` mà backend cấu hình, digest `7cdf5a0187d5c58cc5d369b255592f7841d1c4696d45a8c8a9489440385b22f6`. Ollama 0.32.0 nạp checkpoint GGUF Q4_K_M vào GPU tích hợp của máy ARM64 có 24 GB RAM. Mỗi lượt dùng cùng đoạn nguồn, cùng câu hỏi và giải mã ở temperature 0. Cửa sổ context 4.096 token và trần 80 token đầu ra. Bảy câu khớp chính xác với benchmark oracle trước đó ở các trường câu hỏi, đoạn nguồn, locator và nhãn.

| Checkpoint và prompt | Đúng đủ ý | Đúng phần hỏi trực tiếp | p50 sinh | p50 token đầu |
| --- | ---: | ---: | ---: | ---: |
| 14B, prompt cũ | 4/7 | 6/7 | 4,98 s | 0,93 s |
| 14B, prompt nêu kết luận và ngoại lệ | 4/7 | 6/7 | 5,42 s | 0,97 s |

Prompt bổ sung không tăng điểm, nên lượt RAG dùng prompt cũ. Qwen 1,5B với prompt cũ từng đạt 2/7 đủ ý. So sánh chất lượng này có đồng thời khác biệt về checkpoint, định dạng lượng tử hóa và backend suy luận. Không dùng thời gian PyTorch CPU của model nhỏ để quy phần nhanh chậm cho riêng số tham số.

Ở cả hai prompt, ca hàng tồn kho trả lời đúng phương pháp theo từng mặt hàng nhưng bỏ điều kiện giá trị thuần thấp hơn giá gốc. Ca sự kiện không điều chỉnh trả lời đúng nội dung thuyết minh nhưng không nói rõ rằng số liệu giữ nguyên. Ca Thông tư 99 chạm giới hạn ở cả hai prompt trước khi nói hết ngoại lệ. Hai dòng điểm đáp ứng các ý bắt buộc và phần hỏi trực tiếp được lưu riêng để thấy ảnh hưởng của cách chấm.

[Oracle raw](vas-oracle-qwen14b-dev-v1.json) · [Điểm và lý do](vas-oracle-qwen14b-dev-v1.grades.json)

## RAG trên tập dev

Qdrant nhúng lập chỉ mục 359 chunk với E5-small và BM25 SQLite, rồi ghép thứ hạng qua RRF. So sánh bốn context trên cùng top 5. ID top 5 và số dấu hiệu bằng chứng từng ca khớp với lượt Qwen 0,5B đã lưu. Prompt hệ thống giữ nguyên từ oracle. Độ trễ đầu cuối của runner gồm truy xuất local, chọn đoạn nếu áp dụng, loopback và sinh. Không bao gồm thời gian tải model hoặc xây index.

| Context | Đúng đủ ý | Câu đủ dấu hiệu | Đúng và đủ dấu hiệu | Token đầu vào trung vị | p50 đầu cuối | p50 token đầu |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Preview 200 ký tự mỗi chunk | 4/7 | 0/7 | 0/7 | 384 | 14,61 s | 2,51 s |
| Toàn văn top 5 | 4/7 | 5/7 | 3/7 | 2.509 | 34,58 s | 17,55 s |
| Prefix 512 | 4/7 | 1/7 | 0/7 | 608 | 10,34 s | 1,25 s |
| Chọn đoạn 512 | 4/7 | 2/7 | 1/7 | 584 | 12,48 s | 5,05 s |

Mốc token đầu đo từ lúc gửi request đến Ollama, chưa tính retrieval. Câu trả lời đúng khi thiếu dấu hiệu trong prompt có thể đến từ kiến thức model hoặc cách diễn đạt nguồn mà bộ dò chuỗi không nhận ra. Chỉ số đồng thời giúp kiểm tra rủi ro này, nhưng chưa phải phép chấm claim được hỗ trợ theo ngữ nghĩa hay citation chính xác.

Toàn văn vẫn là mốc chất lượng nguồn. Chọn đoạn giảm thời gian nhưng chưa giữ bằng chứng ngang toàn văn trên dev. Trước khi đọc holdout, cố định prompt cũ, top 5, trần 80 token và ba biến thể model độc lập, toàn văn, chọn đoạn 512. Không chọn lại cấu hình bằng điểm holdout.

[RAG dev raw](vas-context-qwen14b-dev-v1.json) · [Điểm và lý do](vas-context-qwen14b-dev-v1.grades.json)

## Xác nhận trên holdout đã khóa

Giữ nguyên sáu câu holdout, ba tệp PDF và cấu hình truy xuất từ benchmark 0,5B. Runner xác nhận cùng SHA-256 của tập, cùng thứ tự top 5 từng ca và 250 chunk. Đo Qwen 14B trên ba cấu hình đã chốt ở dev. Mỗi cấu hình sử dụng cùng prompt cũ và giới hạn 80 token đầu ra.

| Context | Đúng nghiệp vụ | Câu đủ dấu hiệu | Đúng và đủ dấu hiệu | Token đầu vào trung vị | p50 đầu cuối | p50 token đầu |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Không RAG | 3/6 | 0/6 | 0/6 | 80,5 | 16,95 s | 1,33 s |
| RAG toàn văn top 5 | 5/6 | 6/6 | 5/6 | 2.473,5 | 38,11 s | 26,33 s |
| RAG chọn đoạn 512 | 5/6 | 4/6 | 4/6 | 584 | 17,39 s | 6,26 s |

RAG tăng 2 câu đúng về nghiệp vụ so với model cùng checkpoint chạy độc lập. Chọn đoạn giảm khoảng 76% token đầu vào và 54% p50 so với toàn văn. Hai cấu hình RAG có cùng tổng số câu đúng nhưng sai ở các câu khác nhau. Chọn đoạn trả lời sai ở câu dự phòng cho khoản lỗ hoạt động tương lai. Toàn văn vấp ở câu bình quân gia quyền vì trộn ngôn ngữ và tự đưa hệ số. Một số câu đúng nghiệp vụ còn lỗi ngôn ngữ hoặc lỗi phụ, được đánh dấu trong bảng chấm. Chỉ số đúng và đủ dấu hiệu không đo citation hoặc entailment.

[Holdout raw](vas-holdout-qwen14b-v1.json) · [Điểm và lý do](vas-holdout-qwen14b-v1.grades.json)

**Quyết định:** 14B cho kết quả tốt hơn trong thí nghiệm local. Giữ toàn văn làm mốc bảo toàn bằng chứng và giữ 512 token làm ứng viên tiết kiệm độ trễ. Chưa chọn 512 làm mặc định vì trên cả dev và holdout có ít ca đúng kèm đủ dấu hiệu hơn toàn văn. Chưa đủ dữ liệu để phát hành hoặc fine-tune. Tập sáu câu đã được dùng trong lịch sử đo với model nhỏ và chưa có chấm độc lập. Pipeline benchmark dùng E5 + BM25 SQLite và Qdrant nhúng, chưa đo stack triển khai đầy đủ với bge-m3, TEI, graph và traffic trên SSE.

## Kiểm tra ca Thông tư 99 và adapter của ứng dụng

Giữ nguyên đoạn oracle và prompt cũ ở riêng ca chạm trần. Với mức trần 160 token, 14B tự kết thúc sau 101 token. Câu trả lời có đủ mốc 01/01/2026 và cụm “cho đến khi có văn bản thay thế”. Nó vẫn chưa nói rõ ngoại lệ chỉ áp dụng cho các nội dung được liệt kê tại Điều 31 khoản 2. Đây là chẩn đoán một câu, không dùng để cập nhật điểm của lượt 80 token.

Sau đó gọi `app.llm.providers.ollama.stream_chat` thật của backend với cùng đầu vào. Adapter nhận 100 phần dữ liệu từ Ollama và ghép thành đúng câu trả lời của lượt chẩn đoán. Kiểm tra này xác nhận đường gọi từ adapter đến model local. Chưa đo qua giao diện, middleware, SSE proxy hoặc lưu hội thoại. [Bản ghi chẩn đoán và adapter](vas-tt99-qwen14b-cap160-v1.json)

## Tái lập

Khởi động bản Ollama 0.32.0 được xác minh checksum trên loopback và tải đúng tag. Runner lưu digest từ API Ollama để nhận biết khi tag thay đổi. Biến `HF_HOME` trỏ tới cache của tokenizer và E5-small đã tải. Dùng `HF_HUB_OFFLINE=1` và `PYTHONPATH=apps/backend` như các lượt trước.

```sh
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_oracle.py \
  --ollama-url http://127.0.0.1:11435 \
  --out ingestion/sources/evaluation/vas-oracle-qwen14b-dev-v1.json
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_benchmark.py \
  --context-dev --ollama-url http://127.0.0.1:11435 \
  --out ingestion/sources/evaluation/vas-context-qwen14b-dev-v1.json
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_benchmark.py \
  --ollama-url http://127.0.0.1:11435 --variants base full passages_512 \
  --out ingestion/sources/evaluation/vas-holdout-qwen14b-v1.json
```
