# Compare VAS–IFRS có bằng chứng hai phía

## Triển khai

Compare truy xuất từng phía VAS và IFRS/IAS. Nếu câu hỏi nêu mã, truy xuất riêng mã đó, kiểm tra lại metadata và ưu tiên đưa ít nhất một đoạn mỗi mã vào ngữ cảnh. Retrieval giữ bộ lọc tenant của Qdrant. Khi thiếu mã nguồn, API trả phần đã qua kiểm tra và thông báo chuẩn nào còn thiếu. Yêu cầu thất bại ở tất cả lần truy xuất vẫn đi theo luồng lỗi sẵn có của ứng dụng.

Prompt yêu cầu mỗi dòng chứa một nhận định và mã đoạn. API gửi các nhận định sau khi đã kiểm tra mã trích dẫn thuộc đúng phía. Một dòng kết luận so sánh cần mã hợp lệ từ cả hai phía. Khi model trích tên chuẩn mực, tên đó chỉ được quy về mã đoạn nếu chuẩn mực tương ứng có đúng một đoạn trong ngữ cảnh. Kiểm tra này xác minh nguồn có thể định vị. Việc một đoạn có thực sự hỗ trợ nhận định được chấm riêng dưới đây.

## Đo trước và sau

Chạy agent Compare thật với Qwen2.5-1.5B-Instruct gốc float32 và cùng giới hạn 170 token. Tại ranh giới truy xuất, dùng 18 thẻ tự soạn, embedding E5, BM25 và RRF cục bộ. Reranker dùng thứ tự theo điểm truy xuất cố định. Độ trễ đo toàn bộ lượt agent local từ truy xuất đến final. Lượt này không chạy Qdrant hoặc TEI đang triển khai.

Bộ đầu gồm năm câu Compare của pilot và sáu câu tự do [đã khóa](questions.jsonl). Các lượt đầu đã cung cấp đúng các thẻ kỳ vọng ở cả 11 câu, vì agent cũ có thể lấy tới 10 đoạn. Kết quả pilot top 4 trước đây dùng đường truy xuất khác. Với sáu câu tự do, p50 trong lượt đầu giảm từ 19,52 xuống 6,22 giây, nhưng chỉ một câu có đủ hai mã nguồn và câu đó sai nghiệp vụ. Khi chạy lại bộ kiểm tra cuối trên cùng đầu ra model, hệ thống giữ bốn câu có đủ mã hai phía. Chỉ C21 trả lời đủ ý chính theo rubric. C23 và C24 cho thấy mã hợp lệ vẫn có thể đi cùng nhận định sai. C25 thiếu phát biểu rõ phía VAS loại khoản phi tiền khỏi báo cáo lưu chuyển tiền tệ. C26 báo thiếu IFRS 17 và không chuyển tiếp kết luận không kiểm chứng về chuẩn đó.

Sau khi hoàn thiện kiểm tra mã, khóa riêng [bốn câu tự do mới](holdout.jsonl) rồi chạy trước và sau. Hash đầu vào nằm trong [inputs.sha256](inputs.sha256).

| Chỉ số trên 4 câu mới | Trước | Sau |
| --- | ---: | ---: |
| Đưa đủ hai thẻ vàng vào ngữ cảnh | 4/4 | 4/4 |
| Phát trích dẫn đủ hai thẻ vàng | 0/4 | 2/4 |
| Trả lời đúng và đủ hai trích dẫn hỗ trợ | 0/4 | 2/4 |
| Độ trễ p50 | 15,90 giây | 5,01 giây |

H01 và H04 đúng theo tình huống và dẫn đủ nguồn. H02 và H03 dừng ở thông báo thiếu kết luận có thể kiểm chứng do đầu ra không có trích dẫn hợp lệ, dù thẻ vàng đã có trong ngữ cảnh. Assistant chấm theo đáp án và từng thẻ nguồn. Bốn câu nhỏ và dùng lại các chủ đề đã có trong tập thẻ nên kết quả chỉ phản ánh phép đo local.

[Bản ghi trước](before.json) · [Lượt sửa đầu](after.json) · [Phân tích lại đầu ra bằng bộ kiểm tra cuối](diagnostic-replay.json) · [Bốn câu mới trước sửa](holdout-before.json) · [Bốn câu mới sau sửa](holdout-after.json)

Để tái lập, chạy từ thư mục gốc với `HF_HOME` trỏ vào cache mô hình đã khóa ở pilot trước. Có thể truyền `--agent-file` để kiểm chứng một phiên bản agent được lưu riêng. Baseline dùng file agent và prompt trước thay đổi với SHA-256 bên dưới.

```bash
export HF_HUB_OFFLINE=1 PYTORCH_ENABLE_MPS_FALLBACK=1 PYTHONPATH=apps/backend
export VAS_COMPARE_DIR=ingestion/sources/evaluation/compare-v2
shasum -c "$VAS_COMPARE_DIR/inputs.sha256"
apps/backend/.venv/bin/python "$VAS_COMPARE_DIR/run.py" /private/tmp/vas-compare-repro.json --questions "$VAS_COMPARE_DIR/holdout.jsonl"
```

`383ce70d77d7b0a3223464a9e1104761ee795e88495a7873604ec25f2cd9a78e  ifrs_compare_agent.py`

`1a1c8d9d45b6309b8f993c35af6b41eee253373fd6e1a7da570d725fb5b61b96  ifrs_compare.j2`
