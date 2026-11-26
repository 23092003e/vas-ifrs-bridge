# Pilot VAS–IFRS v1

`pilot-v1.jsonl` có 14 câu tự soạn gồm 10 câu QA, 2 câu đối chiếu và 2 câu cần từ chối tính số tiền khi thiếu dữ liệu. Bộ câu hỏi gồm 8 câu tiếng Việt và 6 câu tiếng Anh. Mỗi dòng có đáp án, ý bắt buộc và định vị nguồn. Đây là tập dev dùng thử rubric, chưa phải tập test độc lập và không dùng để train.

## Định vị bằng chứng

Cả 16 tham chiếu đã được đối chiếu trong 5 tệp local và có đường dẫn tương đối từ `ingestion/sources`. `locator` là số điều hoặc đoạn trong văn bản. `anchor.positions` dùng số trang PDF, dòng HTML gốc hoặc dòng đầu ra từ `textutil -convert txt -stdout`, tùy `anchor.kind`. Các vị trí bắt đầu từ 1. [Tệp khóa](pilot-v1.lock.json) ghi SHA-256 của tập dev và năm tệp nguồn để phát hiện thay đổi. Các vị trí này chưa được ánh xạ sang ID tài liệu hoặc chunk trong Qdrant.

## Kiểm kê và giới hạn của corpus

- Kiểm tra nội dung 5 quyết định VAS theo từng đợt. Các tệp có lần lượt 4, 6, 6, 6 và 4 tiêu đề mở phần nội dung chuẩn mực, tổng cộng 26. [Bảng bao phủ](../vas-coverage.csv) ánh xạ từng mã sang tệp. Quyết định 165 dùng mã chữ Việt cũ. [Bản Unicode từ VCCI](../vas/165-2002-QD-BTC-vcci-unicode.html) có sáu tiêu đề trùng với tệp Chính phủ và được lưu để đối chiếu. Quyết định 12 là Word `.doc`. Quyết định 234 là HTML đăng lại. Chưa xác nhận từng đoạn của các bản đăng lại khớp với bản ký.
- Xác minh Điều 31 khoản 1–2 của Thông tư 99/2025. Áp dụng cho năm tài chính bắt đầu từ hoặc sau 01/01/2026. Giữ văn bản cũ riêng theo thời kỳ. Một số nội dung cổ phần hóa doanh nghiệp nhà nước theo Thông tư 200 tiếp tục thực hiện cho đến khi có văn bản thay thế. Cần bổ sung văn bản lịch sử và các sửa đổi theo phạm vi đánh giá trước khi dùng TT200 làm nguồn cho câu hỏi theo kỳ.
- Đã lưu [bản hợp nhất EU 2023/1803](../ifrs/eu-2023-1803-consolidated-2026-03-08.en.html) và [văn bản EU thông qua IFRS 18](../ifrs/eu-2026-338-ifrs18.en.html) dạng HTML tiếng Anh từ Publications Office. Hai bản được đánh dấu phục vụ tra cứu cá nhân. Phiên bản EU có phạm vi thông qua riêng. [Điều kiện tái sử dụng của EUR-Lex](https://eur-lex.europa.eu/content/legal-notice/legal-notice.html?locale=en) nêu ngoại lệ cho International Accounting Standards. Bản hợp nhất có điều khoản riêng đối với sử dụng ngoài EEA. Quyền dùng cho RAG và fine-tuning chưa được xác nhận.
- [Manifest tải xuống](../downloads.json) khóa checksum các bản nguồn thu được. Bộ toàn văn IASB Issued 2026 và nguồn chính thức cho các bản VAS đăng lại vẫn còn thiếu. Chưa khóa corpus cuối cùng hoặc chạy ingestion.

## Cách dùng khi dữ liệu đã sẵn sàng

1. Xác nhận quyền và phiên bản nguồn. Giữ snapshot cho từng kỳ và từng khu vực áp dụng. Lưu manifest bất biến với checksum, phiên bản parser, chuẩn mực và phạm vi hiệu lực.
2. Đối chiếu locator với văn bản đã chuẩn hóa, ánh xạ thành ID tài liệu/đoạn ổn định. Chỉ sau đó xuất `ground_truth_doc_ids` và nhãn đoạn cho runner retrieval. Với câu từ chối, chấm đúng việc nêu dữ liệu còn thiếu.
3. Thử rubric với 14 câu pilot, sau đó tạo tập test riêng do người khác gắn nhãn hoặc rà soát. Khóa test trước khi chọn cấu hình. Theo dõi chất lượng theo ngôn ngữ, tác vụ, phiên bản và chủ đề. Không dùng điểm pilot làm kết luận về toàn bộ VAS/IFRS.

Benchmark FastAPI SSE dùng bảy câu VAS từ pilot làm dev và sáu câu mới làm holdout. Xem [phương pháp và kết quả](VAS_API_BENCHMARK.md), [holdout](vas-api-new-v1.jsonl) và [checksum nguồn](vas-api-new-v1.lock.json).
