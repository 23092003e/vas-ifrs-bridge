# Chọn đoạn bằng chứng trong ngân sách 512 token

## Kết quả

Đã chạy 28 lượt sinh trên bảy câu dev. Cùng index 359 chunk và cùng top 5 hybrid cho từng câu.

| Context | Câu đủ bằng chứng | Dấu hiệu xuất hiện | Câu đúng đầy đủ | Token đầu vào trung vị | p50 | p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Preview | 0/7 | 0/14 | 1/7 | 384 | 7,62 s | 9,02 s |
| Toàn văn | 5/7 | 9/14 | 1/7 | 2.509 | 54,33 s | 61,98 s |
| Prefix 512 | 1/7 | 4/14 | 0/7 | 608 | 10,35 s | 12,21 s |
| Chọn đoạn 512 | 2/7 | 6/14 | 0/7 | 584 | 11,40 s | 12,25 s |

Trong cùng mức trần 512 token, xếp hạng đoạn giữ thêm 2 dấu hiệu và thêm 1 câu đủ bằng chứng so với lấy phần đầu. So với toàn văn, nó dùng ít hơn khoảng 77% token đầu vào và giảm khoảng 79% độ trễ p50, nhưng làm mất 3 câu đủ bằng chứng và 1 câu đúng đầy đủ. Thời gian chọn đoạn riêng là 19–28 ms. Các số trên là một lượt chạy CPU, chưa kiểm tra dao động giữa các lượt.

Ở câu VAS 14, bộ chọn giữ đủ hai dấu hiệu nhưng model vẫn từ chối trả lời. Ở câu Thông tư 99, nó giữ đủ ba dấu hiệu nhưng model chỉ nêu đúng mốc áp dụng và bỏ sót ngoại lệ Thông tư 200. Hai câu thiếu dấu hiệu ngay với toàn văn top 5 nằm ở giới hạn của retrieval hoặc phép đối chiếu chuỗi. Chỉ số này đếm cụm từ được gán nhãn, nên không nhận diện được mọi cách diễn đạt tương đương.

**Quyết định:** Chưa chọn bộ đoạn 512 token làm mặc định. Trên dev, ứng viên giảm độ trễ nhưng chưa giữ được mức chất lượng của toàn văn. Kết quả hỗ trợ thử tiếp cách giữ các đoạn lân cận và ngữ cảnh cho câu nhiều điều kiện. Cần dùng model mạnh hơn để xác định phần lỗi do model đọc nguồn trước khi thử trên tập test mới.

[Kết quả từng câu](vas-context-dev-v1.json) và [lý do chấm từng biến thể](vas-context-dev-v1.grades.json) đã lưu. Việc chấm do trợ lý thực hiện trên bản hiển thị đã xáo trộn nhãn cấu hình, chưa có rà soát độc lập.

## Thiết kế

Thí nghiệm dùng bảy câu VAS từ tập `pilot-v1.jsonl`. Bộ sáu câu holdout của benchmark trước không tham gia. Bốn nguồn VAS được xác minh checksum trước khi lập chỉ mục local. Cùng một model Qwen2.5-0.5B-Instruct, prompt, giới hạn 80 token đầu ra và danh sách top 5 hybrid được dùng cho từng câu. Luân phiên thứ tự chạy giữa các câu.

| Biến thể | Nội dung đưa vào prompt |
| --- | --- |
| Preview | 200 ký tự đầu mỗi chunk |
| Toàn văn | Toàn bộ top 5 chunk |
| Prefix 512 | 512 token đầu của phần toàn văn đã nối |
| Chọn đoạn 512 | Xếp hạng các cửa sổ 70 từ, bước trượt 50 từ, bằng BM25 theo câu hỏi. Bỏ qua cửa sổ chồng lặp trong cùng chunk và ghép đến tối đa 512 token |

Prefix và chọn đoạn dùng cùng **giới hạn tối đa**, mức tiêu thụ thực tế có thể khác. Giới hạn chỉ tính context bằng tokenizer của Qwen. Số token đầu vào được báo gồm cả prompt và câu hỏi. Bộ chọn đoạn chỉ đọc câu hỏi và các chunk truy xuất. Nó không dùng đáp án hoặc nhãn bằng chứng.

Xác minh trước 14 dấu hiệu bằng chứng trong tệp nguồn. Đếm số dấu hiệu xuất hiện và số câu có đủ dấu hiệu. Đây là phép đo bảo toàn bằng chứng, riêng với chấm câu trả lời đúng đầy đủ. Chấm theo các ý bắt buộc trong pilot và không chấp nhận mâu thuẫn. Độ trễ CPU gồm truy xuất, chọn đoạn nếu áp dụng và sinh câu trả lời. Không gồm tải model, tạo index hoặc độ trễ mạng.

Ứng viên chỉ đủ điều kiện mang đi kiểm tra trên test mới khi giữ chất lượng bằng chứng và câu trả lời của toàn văn, đồng thời dùng ít token và giảm độ trễ. Không suy rộng từ tập dev bảy câu sang model triển khai.

```sh
HF_HOME=/private/tmp/vas-benchmark-hf HF_HUB_OFFLINE=1 PYTHONPATH=apps/backend \
  apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_benchmark.py \
  --context-dev --out ingestion/sources/evaluation/vas-context-dev-v1.json
```
