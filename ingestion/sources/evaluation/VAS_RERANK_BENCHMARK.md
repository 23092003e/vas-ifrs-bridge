# Tác động của reranker lên QA VAS

Đo lại 7 câu dev và 6 câu từ holdout đã công bố của [benchmark FastAPI SSE](VAS_API_BENCHMARK.md). Agent thật chạy truy xuất Qdrant dense bge-m3 và BM25 kết hợp bằng RRF. Runner thu danh sách ứng viên tại biên rerank, trước khi gọi model sinh câu trả lời. Cả ba chính sách dùng cùng ứng viên cho từng câu và cùng giới hạn đầu ra 8 chunk.

- **RRF** lấy 8 chunk đầu theo điểm truy xuất, tương ứng đường fallback của reranker trên corpus này.
- **TEI có ngưỡng** tái lập cấu hình SSE trước. TEI chấm 8 ứng viên đầu, tối đa 96 từ mỗi ứng viên, với đoạn toàn văn được giữ để tính độ phủ. Dùng ngưỡng `0.10`, hạ xuống `0.01` khi dưới ba chunk đạt ngưỡng chính.
- **TEI bổ sung RRF** giữ thứ hạng của các chunk qua ngưỡng, rồi lấp các vị trí còn thiếu bằng RRF. Hai chính sách TEI dùng lại đúng điểm của cùng một request.

## Truy xuất

| Chính sách | Dấu hiệu dev | Câu dev đủ dấu hiệu | Dấu hiệu holdout chạy lại | Câu holdout đủ dấu hiệu |
| --- | ---: | ---: | ---: | ---: |
| Toàn bộ 40 ứng viên | 12/14 | 6/7 | 11/11 | 6/6 |
| RRF top 8 | 12/14 | 6/7 | 10/11 | 5/6 |
| TEI có ngưỡng | 6/14 | 1/7 | 10/11 | 5/6 |
| TEI bổ sung RRF | 12/14 | 6/7 | 10/11 | 5/6 |

Trên dev, câu lập dự phòng theo từng mặt hàng có đủ hai dấu hiệu ở hạng 1 của Qdrant. Sau khi lọc TEI chỉ còn một chunk và mất cả hai. Câu doanh thu mất một trong hai dấu hiệu. Với câu chiết khấu thương mại ở holdout, dấu hiệu bị thiếu nằm ở hạng 29 và 32, ngoài phạm vi TEI chấm. Bổ sung bằng RRF top 8 giải quyết phần bị ngưỡng loại trên dev, nhưng không tăng độ phủ ở câu chiết khấu.

Thời gian p50 từ lúc gọi agent đến danh sách ứng viên là 0,30 giây trên dev và 0,33 giây trên holdout. TEI riêng chiếm thêm 5,37 và 6,41 giây trên máy thử ở lượt này. RRF giữ nhiều văn bản hơn. Trung vị độ dài chunk gộp trên dev tăng từ 5.175 lên 13.725 ký tự so với TEI có ngưỡng, nên chênh lệch thời gian truy xuất chưa nói được độ trễ đầu cuối.

Thứ tự chunk sau lọc TEI khớp chính xác với bản ghi SSE trước ở 11/13 câu. So sánh ba chính sách tại đây dùng chung ứng viên trong từng câu. Dấu hiệu là phép so khớp văn bản, chưa đánh giá ngữ nghĩa hoặc mức hỗ trợ của citation. Holdout đã được dùng ở lượt trước và được chạy lại để chẩn đoán retrieval.

[Bản ghi truy xuất theo câu](vas-rerank-v1.json)

## Kết quả đầu cuối trên dev

Chạy thêm 7 lượt FastAPI SSE với top 8 RRF toàn văn và giới hạn 160 token sinh. Đối chiếu với 7 lượt toàn văn có TEI từ benchmark trước, cùng Qwen 14B và corpus, ở hai thời điểm khác nhau. RRF-only mô phỏng đường fallback bằng runner, không gửi request đến TEI.

| Context toàn văn | Đúng nghiệp vụ | Dấu hiệu trong prompt | Câu phát citation qua SSE | Context p50 | TTFT p50 | Tổng p50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TEI có ngưỡng | 3/7 | 6/14 | 4/7 | 1.537 token | 34,62 s | 60,65 s |
| RRF top 8 | 3/7 | 12/14 | 0/7 | 4.088 token | 26,15 s | 55,23 s |

Cả 7 lượt RRF phát câu trả lời và lưu được hội thoại. Sáu prompt hệ thống dài hơn 4.096 token trước khi gửi, nên độ phủ đo được ở prompt không đồng nghĩa model đã thấy đủ bằng chứng. RRF giữ gấp đôi dấu hiệu và giảm p50 tổng khoảng 9% trong đối chiếu này, nhưng không cải thiện tổng số câu đúng và không phát được citation hợp lệ. Ví dụ, câu doanh thu có cả hai dấu hiệu trong prompt dựng mà vẫn trả lời sai điều kiện. Giữ cấu hình reranker hiện tại trong ứng dụng. Phương án bổ sung bằng RRF mới được đo ở bước truy xuất.

[Bản ghi SSE RRF](vas-api-rrf-dev-v1.json) · [Điểm từng câu](vas-api-rrf-dev-v1.grades.json)

## Tính tái lập của câu truy vấn

Cùng một câu về hàng tồn kho, ontology trước đây sinh ba chuỗi mở rộng khác nhau khi chạy ba tiến trình với `PYTHONHASHSEED=0`, `1` và `2`. Cả ba có cùng độ dài và cùng tập từ, với thứ tự khác nhau. Đã sắp xếp phần từ bổ sung trước khi ghép vào truy vấn. Sau sửa, cả ba tiến trình sinh chuỗi có cùng SHA-256. Ba lượt truy xuất thật vẫn cho hai thứ tự top 8, nên độ tái lập mới được xác nhận ở chuỗi truy vấn. Các lượt benchmark trên bảng dùng mã trước sửa. Test mới thất bại trước sửa và sau đó qua cùng toàn bộ 122 unit test. [Test hồi quy](../../../apps/backend/tests/unit/rag/test_ontology_service.py)

## Cách chạy lại

Dùng stack và chỉ mục local đã dựng ở [benchmark FastAPI SSE](VAS_API_BENCHMARK.md). Với biến môi trường từ báo cáo đó, chạy:

```sh
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_rerank_eval.py \
  --out ingestion/sources/evaluation/vas-rerank-v1.json
apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_api_eval.py \
  --rrf-only --max-tokens 160 --out ingestion/sources/evaluation/vas-api-rrf-dev-v1.json
```
