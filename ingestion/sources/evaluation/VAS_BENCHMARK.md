# Benchmark VAS local

## Kết quả lần chạy v1

Qdrant nhúng lập chỉ mục 250 chunk trong 8,3 giây. Mỗi cấu hình truy xuất chạy cùng 6 câu.

| Retrieval | Có đoạn đúng trong top 5 | MRR@5 |
| --- | ---: | ---: |
| Sparse BM25 | 4/6 | 0,500 |
| Dense E5-small | 6/6 | 0,806 |
| Hybrid dense + sparse với RRF | 6/6 | 0,833 |

Hybrid tăng MRR@5 khoảng 0,028 so với dense. Nó đưa đoạn đúng ở câu h06 từ hạng 3 lên hạng 1, nhưng đẩy h03 từ hạng 1 xuống hạng 2. Không thay đổi số câu tìm được bằng chứng trong top 5.

| Context Qwen | Có đoạn bằng chứng trong prompt | Đúng đầy đủ | Đúng hướng | Token đầu vào trung vị | p50 | p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Không context | 0/6 | 0/6 | 0/6 | 80,5 | 3,12 s | 3,45 s |
| Hybrid + preview | 0/6 | 0/6 | 1/6 | 377 | 6,78 s | 8,12 s |
| Hybrid + toàn văn | 6/6 | 1/6 | 2/6 | 2.473,5 | 43,99 s | 53,79 s |

Toàn văn cải thiện hơn preview 1 câu đúng đầy đủ. Token đầu vào tăng khoảng 6,6 lần và độ trễ p50 tăng khoảng 6,5 lần. `Đúng hướng` tính cả câu đạt tiêu chí đầy đủ; nhãn này chỉ cho thấy kết luận cơ bản đi đúng hướng dù câu trả lời còn thiếu hoặc giải thích sai. Câu h03 có bằng chứng ở hạng 2 với toàn văn nhưng model vẫn không trả lời đúng. Đây là lý do cần chấm câu trả lời riêng với điểm truy xuất.

Kết quả đủ để kiểm chứng việc preview làm mất bằng chứng trên các fixture này. Chưa đủ căn cứ để chọn gửi toàn văn của mọi chunk theo mặc định. Thí nghiệm tiếp theo nên so context gồm đoạn liên quan trong cùng ngân sách token trên tập dev, rồi đo lại trên tập test mới. Kế hoạch fine-tuning giữ nguyên thiết kế base/adapter × có/không RAG. Chưa có tập train riêng hoặc tập test đủ lớn do người độc lập kiểm tra để đánh giá việc thay trọng số.

[Dữ liệu từng lượt chạy](vas-benchmark-v1.json) và [điểm, lý do từng câu](vas-benchmark-v1.grades.json) được lưu riêng. Tên cấu hình được xáo trộn theo câu trước khi chấm bởi cùng trợ lý đã soạn câu hỏi. Chưa có chấm mù độc lập của chuyên gia.

## Phạm vi và cách đo

- Tập `vas-holdout-v1.jsonl` gồm 6 câu mới, dùng các đoạn VAS 11, 18 và 30 từ Quyết định 100/2005. Các nguồn và chủ đề này chưa xuất hiện trong 14 câu dev ở `pilot-v1.jsonl`. Cùng trợ lý soạn và chấm nên đây là holdout nội bộ nhỏ, chưa phải bộ kiểm định độc lập do chuyên gia xác nhận. Không dùng để huấn luyện.
- Index dùng ba PDF đã tải, gồm quyết định 149, quyết định 100 và phần 1 Thông tư 99. Kiểm tra SHA-256 theo manifest trước khi đọc. Dùng chunker của dự án. Mỗi câu có chuỗi bằng chứng xác định chunk đúng; câu có thể có nhiều chunk đúng do overlap. Dùng Hit@5 và MRR@5 để đo xem bằng chứng xuất hiện và đứng ở đâu. Hit@5 khác với recall trên toàn bộ đoạn liên quan đã gán nhãn.
- So sánh BM25 SQLite, dense E5-small qua Qdrant nhúng và phối hợp hai thứ hạng bằng RRF. Đây là thí nghiệm thay thế local. Nó chưa đo BM25 FastEmbed, bge-m3, TEI, graph, ontology hoặc SSE của stack triển khai.
- Đo sinh câu trả lời với Qwen2.5-0.5B-Instruct. Dùng cùng câu hỏi, prompt hệ thống, giới hạn 80 token đầu ra và giải mã greedy. So ba điều kiện không context, hybrid với preview 200 ký tự mỗi chunk, và hybrid với đầy đủ nội dung của cùng top 5 chunk. Xoay thứ tự điều kiện qua các câu và chạy một câu làm nóng trước. Độ trễ là thời gian sinh toàn bộ câu trả lời cộng retrieval cho biến thể RAG. Không tính thời gian tải model hoặc lập index. Không có đo TTFT hay độ trễ qua mạng.
- Chấm mỗi câu đúng khi có đủ kết luận và điều kiện cần thiết, không có sai sót mâu thuẫn với đáp án. Đếm riêng bằng chứng xuất hiện trong prompt để tách chất lượng retrieval khỏi chất lượng model đọc nguồn. Sáu mẫu không đủ để suy rộng về các chuẩn mực khác.

## Tái lập

Model nguồn và checkpoint được khóa trong runner. Cài các checkpoint vào cache Hugging Face, sau đó chạy từ repo với `pdftotext`, môi trường Python backend, PyTorch và Transformers. Bản chạy này dùng CPU, 4 luồng.

```sh
HF_HOME=/private/tmp/vas-benchmark-hf HF_HUB_OFFLINE=1 PYTHONPATH=apps/backend \
  apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_benchmark.py \
  --out ingestion/sources/evaluation/vas-benchmark-v1.json
```

Trước khi đo fine-tuning, chuẩn bị bộ train riêng theo nhóm tài liệu/chủ đề và tập test lớn hơn. Dùng cùng corpus và cấu hình RAG ở hai checkpoint để tách ảnh hưởng trọng số. Các tệp IFRS hiện đang được lưu phục vụ tra cứu, nằm ngoài thí nghiệm này.
