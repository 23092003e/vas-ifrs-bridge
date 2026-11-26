# Tài liệu nguồn VAS và IFRS

Thu thập ngày 2026-11-19. Các tệp nằm ngoài `ingestion/raw` để chúng không bị nạp cùng corpus cũ. [Manifest tải xuống](downloads.json) ghi URL, kích thước, SHA-256 và cả các lần tải thất bại.

Các bản nguồn gốc được lưu cục bộ. Để chuẩn bị dữ liệu cho một bản clone mới, tải các tệp được phép sử dụng theo manifest và đặt vào đúng đường dẫn tương đối trong thư mục này.

## VAS

Đã lưu 5 quyết định bao phủ 26 chuẩn mực. Đã kiểm tra tiêu đề và sự hiện diện của các phần nội dung trong tệp. Các bản đăng lại cần đối chiếu với bản gốc trước khi chọn làm nguồn trích dẫn chính thức.

| Quyết định | VAS | Tệp và nguồn |
| --- | --- | --- |
| 149/2001/QĐ-BTC | 02, 03, 04, 14 | [PDF](vas/149-2001-QD-BTC.pdf) từ bản đăng lại, đối chiếu danh mục [CSDL quốc gia](https://vbpl.moj.gov.vn/botaichinh/Pages/vbpq-toanvan.aspx?ItemID=22028) |
| 165/2002/QĐ-BTC | 01, 06, 10, 15, 16, 24 | [RTF](vas/165-2002-QD-BTC.rtf) từ [Cổng Chính phủ](https://vanban.chinhphu.vn/default.aspx?docid=11581&pageid=27160), dùng mã chữ Việt cũ |
| 234/2003/QĐ-BTC | 05, 07, 08, 21, 25, 26 | [HTML](vas/234-2003-QD-BTC.html) từ bản đăng lại, đối chiếu [CSDL quốc gia](https://vbpl.moj.gov.vn/quangngai/Pages/vbpq-luocdo.aspx?ItemID=17841) |
| 12/2005/QĐ-BTC | 17, 22, 23, 27, 28, 29 | [DOC](vas/12-2005-QD-BTC.doc) từ bản đăng lại |
| 100/2005/QĐ-BTC | 11, 18, 19, 30 | [PDF](vas/100-2005-QD-BTC.pdf) từ bản đăng lại, đối chiếu [CSDL quốc gia](https://vbpl.moj.gov.vn/botuphap/Pages/vbpq-vanbanlienquan.aspx?ItemID=16846) |

Đã lưu thêm 10 phần PDF của [Thông tư 99/2025/TT-BTC](https://congbao.chinhphu.vn/van-ban/thong-tu-so-99-2025-tt-btc-46529/59652.htm), [Luật Kế toán 88/2015/QH13](vas/88-2015-QH13.pdf) và [Thông tư 161/2007/TT-BTC](vas/161-2007-TT-BTC.html). Đây là nhóm văn bản bổ trợ. Phạm vi hiện tại chưa bao gồm toàn bộ văn bản sửa đổi, chế độ chuyên ngành và văn bản lịch sử.

Chỉ mục thử nghiệm cho benchmark VAS dùng bốn tệp và 359 chunk. Xem phạm vi, số đo và cách chạy lại trong [benchmark FastAPI SSE](evaluation/VAS_API_BENCHMARK.md).

## IFRS Accounting Standards

Đã lưu [danh mục Issued 2026 tiếng Anh](ifrs/issued-2026-catalog.html) từ [IFRS Foundation](https://www.ifrs.org/issued-standards/search-results/). Trang liệt kê 174 mục gồm chuẩn mực, khung khái niệm, diễn giải và tài liệu đi kèm. Con số này là số mục danh mục. Thư mục `ingestion/raw/shared/ifrs` hiện có 8 PDF và 1 Markdown từ trước, chưa đối chiếu phiên bản hoặc quyền sử dụng với bộ Issued 2026.

Toàn văn Part A của năm hiện tại được cung cấp cho tài khoản đăng ký. Tài liệu đi kèm có thể cần subscription. Điều 5.3 và 6 của [điều khoản IFRS Foundation](https://www.ifrs.org/legal/terms-and-conditions/) giới hạn việc tải tự động và tích hợp nội dung. Để hoàn tất corpus, cần bản xuất hoặc gói tài liệu được phép dùng cho mục đích dự án. Xác nhận riêng phạm vi được phép cho RAG, evaluation và fine-tuning trước khi đưa file vào pipeline.

Đã bổ sung bản tiếng Anh [EU 2023/1803 hợp nhất 08/03/2026](ifrs/eu-2023-1803-consolidated-2026-03-08.en.html) và [EU 2026/338 về IFRS 18](ifrs/eu-2026-338-ifrs18.en.html) từ Publications Office để tra cứu cá nhân. Đây là bản được EU thông qua, có phiên bản và điều kiện sử dụng riêng.

Chưa nhập các tệp này vào Qdrant, tạo embedding, chạy benchmark hoặc fine-tuning.

Xem [bảng bao phủ 26 VAS](vas-coverage.csv) và [rà soát nguồn và bộ câu hỏi pilot](evaluation/README.md) để biết những phần đã xác minh, định vị đoạn nguồn và các điều kiện còn thiếu để khóa corpus.
