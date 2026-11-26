# Pilot VAS–IFRS với ma trận 2×2

Pilot đo đóng góp của truy xuất và fine-tuning trên cùng bài trắc nghiệm. Mỗi đầu ra chọn một đáp án và liệt kê mã thẻ bằng chứng. Qwen2.5-1.5B-Instruct là checkpoint gốc. Cùng checkpoint đó được gắn LoRA sau khi hoàn tất baseline. Pipeline thử nghiệm dùng multilingual-e5-small, BM25 và RRF top 4 trên 18 thẻ kiến thức. Prompt, trần sinh 32 token và thứ tự thử nghiệm giữ nguyên giữa hai checkpoint.

## Nguồn và dữ liệu

[Bảng kiểm kê](coverage.json) ghi 26 tiêu đề VAS, 174 mục danh mục IFRS và checksum của các tệp tham chiếu. Pilot truy xuất 7 thẻ VAS và 11 thẻ IFRS/IAS do assistant viết lại theo nội dung nghiệp vụ, kèm phiên bản nguồn và số đoạn. Nội dung toàn văn của IFRS Foundation và phần phụ lục IAS/IFRS của EU được giữ ngoài tập train và chỉ mục. Đây là pilot trên tài liệu dẫn chiếu, chưa thay thế corpus IFRS chính thức hoặc đánh giá đầy đủ hệ thống truy xuất của ứng dụng. [Điều khoản IFRS Foundation](https://www.ifrs.org/legal/terms-and-conditions/) · [Bản IFRS được EU thông qua](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02023R1803-20260308)

| Tập | Số câu | Cách dùng |
| --- | ---: | --- |
| Train | 64 | Tình huống giả lập, học chọn đáp án, bám thẻ và nhận ra khi thiếu dữ kiện. Bốn nhóm chủ đề giả lập |
| Dev | 16 | Hai nhóm giả lập khác, chỉ dùng đo khả năng chuyển sang ví dụ chưa gặp |
| Test | 20 | Mười câu Việt, mười câu Anh. Bốn nhóm bằng nhau gồm VAS, IFRS/IAS, Compare và tình huống thiếu dữ kiện |

Tập test do assistant soạn và đối chiếu theo đoạn nguồn. Nhãn trắc nghiệm kiểm tra được tự động và chưa có kế toán viên rà soát độc lập. Câu hỏi test theo chủ đề kế toán, còn train và dev lấy bối cảnh giả lập ngoài VAS–IFRS nhằm đo kỹ năng bám bằng chứng. Chỉ mục chứa thẻ bằng chứng và thông tin nhiễu. [Tệp khóa](lock.json) ghi SHA-256 của bốn tệp dữ liệu và runner. Runner kiểm tra nhóm, ID, câu hỏi không trùng giữa các tập và các mã bằng chứng test có trong corpus.

## Cách chạy lại

Tải hai checkpoint công khai đúng revision trong [runner](run_matrix.py) vào cache Hugging Face. Từ thư mục gốc repo, đặt `HF_HOME` theo vị trí cache rồi chạy các lệnh theo thứ tự.

```bash
export HF_HUB_OFFLINE=1 PYTORCH_ENABLE_MPS_FALLBACK=1
export VAS_MATRIX_RUN=/private/tmp/vas-matrix-v1-repro
apps/backend/.venv/bin/python ingestion/sources/evaluation/matrix-v1/run_matrix.py base --work "$VAS_MATRIX_RUN"
apps/backend/.venv/bin/python ingestion/sources/evaluation/matrix-v1/run_matrix.py train --work "$VAS_MATRIX_RUN"
apps/backend/.venv/bin/python ingestion/sources/evaluation/matrix-v1/run_matrix.py tuned --work "$VAS_MATRIX_RUN"
```

Các lượt dùng GPU Metal, float32 cho mô hình sinh và CPU cho mô hình embedding. Mỗi checkpoint có một lượt làm nóng trước khi đo. Độ trễ tổng bao gồm truy xuất từng câu, tạo prompt và sinh câu trả lời. Tính TTFT dựa trên thời điểm streamer nhận token đầu, chưa bao gồm mạng hoặc SSE. Tham số LoRA được chốt trước khi đo và giữ cố định trong hai epoch. Điểm chất lượng đo khả năng chọn đáp án trong bài trắc nghiệm có tập đáp án cố định. Kết quả Compare yêu cầu đúng cả hai mã thẻ để được tính là đúng có đủ bằng chứng.

## Kết quả trên cùng 20 câu test

| Cấu hình | Đáp án đúng | Đúng định dạng | Đúng kèm đủ bằng chứng | Tổng p50 / p95 |
| --- | ---: | ---: | ---: | ---: |
| Base, không RAG | 11/20 | 0/20 | — | 0,268 / 0,766 s |
| Base, hybrid RAG | 15/20 | 0/20 | 0/20 | 0,531 / 0,721 s |
| LoRA, không RAG | 15/20 | 20/20 | — | 0,410 / 0,560 s |
| LoRA, hybrid RAG | 17/20 | 19/20 | 4/20 | 0,760 / 0,918 s |

- Hybrid RAG tăng 20 điểm phần trăm với base và 10 điểm với LoRA. Trong cặp base, 5 câu cải thiện và 1 câu giảm. Truy xuất top 4 đạt recall trung bình theo câu 87,5% và đủ thẻ cho 16/20 câu. Compare chỉ lấy đủ cả hai thẻ ở 2/5 câu.
- LoRA tăng 20 điểm phần trăm khi chạy riêng và 10 điểm khi đã có RAG. Trên RAG, 3 câu cải thiện và 1 câu giảm vì model trả sai cấu trúc ở T10. Đáp án dạng một chữ cái được chấm ở cột đáp án. Sau khi thấy base bỏ hậu tố trích dẫn, phép chấm đáp án được bổ sung bằng cùng bộ phân tích ký tự đầu cho mọi nhánh. Điểm định dạng và bằng chứng tiếp tục dùng quy tắc ban đầu.
- LoRA + RAG phát 11 mã trích dẫn, 6 mã khớp bằng chứng kỳ vọng trong các thẻ được truy xuất. Cả 5 câu Compare chọn đúng, 0/5 có đủ hai trích dẫn đúng. Nhóm thiếu dữ kiện giữ 4/5 ở cả bốn cấu hình. Nhánh kết hợp đạt 10/10 tiếng Anh và 7/10 tiếng Việt trong pilot.
- LoRA tăng p50 của nhánh RAG khoảng 0,23 giây. TTFT p50 của hai nhánh RAG lần lượt là 0,445 và 0,438 giây. Số token đầu ra p50 tăng từ 2 lên 6 khi model bắt đầu phát mã trích dẫn. Các số latency đo trên một máy với batch inference 1; P95 từ 20 mẫu dễ dao động.

LoRA rank 8 tác động vào Q/V của 8 lớp cuối, huấn luyện 311.296 tham số trong 2 epoch và 32 bước cập nhật. Loss trung bình giảm từ 0,5184 xuống 0,0878. Huấn luyện mất 35,1 giây trên Metal. Dev chọn đáp án đúng 12/16 trước và 14/16 sau. Lượt float16 thử trước đó cho đầu ra lặp và loss không hữu hạn, nên cả bốn ô dùng float32.

[Bản ghi baseline](base.json) · [Các bước train](train.json) · [Adapter LoRA](adapter.safetensors) · [Bản ghi sau LoRA](tuned.json) · [Số liệu và các cặp thay đổi](summary.json)

Cấu hình thử nghiệm chưa được đưa lên ứng dụng. Trắc nghiệm ngắn có đáp án định sẵn, tập nhãn chưa được chuyên gia chấm độc lập và RAG chạy trên corpus thẻ nhỏ. Phép đo đầu cuối của FastAPI/Qdrant trên toàn văn VAS–IFRS và benchmark sinh câu trả lời tự do vẫn cần nguồn được phép dùng và một tập đánh giá lớn hơn.
