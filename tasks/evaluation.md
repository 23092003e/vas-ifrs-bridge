# Đánh giá đóng góp kỹ thuật của VAS-IFRS Bridge

## Thiết kế thí nghiệm

Giữ cố định phiên bản model sinh, tham số sinh, giới hạn output, corpus, câu hỏi và rubric. Chạy các cấu hình trên cùng câu hỏi, xáo trộn thứ tự và ẩn cấu hình khi chấm. Ghi SHA, phiên bản dữ liệu/index, model/digest, thiết bị, chế độ cache và thời điểm chạy. Dùng cùng ngân sách context cho các thí nghiệm loại bỏ thành phần. Riêng thí nghiệm preview so với full text cần ghi số token thực tế để đo chi phí của thay đổi.

| Cấu hình | Dùng để đo |
| --- | --- |
| A. Model gốc, prompt trung tính, không retrieval | Mốc chất lượng và tốc độ của model trên cùng câu hỏi |
| B. Model gốc, prompt nghiệp vụ, không retrieval | B − A đo đóng góp của prompt. Dùng rubric về độ đúng và khả năng từ chối cho cả hai |
| C. B + dense RAG | C − B đo giá trị bổ sung từ retrieval và corpus ở cấu hình tối giản |
| D. Pipeline repo tại `d5d1ca4` | D − A đo hiệu quả tổng thể. So D với D bỏ từng thành phần để đo riêng BM25/RRF, reranker, ontology/query expansion, graph và hậu xử lý citation. Giữ các thành phần khác cố định |
| E. D + một thay đổi | E − D đo đóng góp của riêng bản sửa. Bước đầu là preview → full text |
| F. Model đã fine-tune | Dùng thiết kế 2×2 bên dưới để đo trọng số và pipeline độc lập |

Graph và ontology cần được đo qua đường QA có gọi chúng. Runner retrieval hiện tại gọi `retrieve_multi`, nên không bao quát hai thành phần này. Dùng tập khóa riêng cho từng luồng QA, Compare và từ chối trả lời. Các biến thể không retrieval vẫn được chấm độ đúng và từ chối. Chỉ tính metric retrieval hoặc citation khi cấu hình có đầu ra tương ứng và công bố tỷ lệ có citation cùng tỷ lệ citation đúng.

## Dữ liệu và cách chấm

- Chia train/dev/test theo nhóm tài liệu hoặc chủ đề và loại câu hỏi trùng, kể cả câu diễn đạt lại. Train dùng để học trọng số, dev để chọn prompt, `k`, ngưỡng rerank hoặc checkpoint. Giữ test cố định và khóa nhãn trước khi chọn cấu hình. Với RAG, corpus có thể chứa tài liệu nguồn của test; giữ riêng câu hỏi, đáp án và nhãn test khỏi dữ liệu tuning.
- Gắn ID câu hỏi, ngôn ngữ, loại tác vụ, phiên bản chuẩn mực, đáp án theo các ý bắt buộc và bằng chứng đoạn/điều. Có câu thiếu bằng chứng, có ngoại lệ và câu cần đối chiếu nhiều nguồn. Dùng dữ liệu giả hoặc đã được phép cho tình huống tenant. Nhờ người có chuyên môn chấm mù một mẫu và đối chiếu đánh giá tự động theo cùng rubric.
- Đo Recall@k và MRR ở mức đoạn; báo riêng mức tài liệu, loại ID trùng khi xếp hạng tài liệu. Đo tỷ lệ ý bắt buộc đúng, claim có nguồn hỗ trợ, citation đúng đoạn, từ chối đúng và sai, tỷ lệ lỗi, TTFT, tổng độ trễ p50/p95 và token/câu. Báo số mẫu, nhóm ngôn ngữ/tác vụ, chênh lệch theo cặp và khoảng tin cậy bootstrap khi đủ mẫu. Tách lượt cache lạnh và nóng. Chốt ngưỡng hồi quy chất lượng, độ trễ và chi phí trên dev trước khi xem test.
- Lưu câu trả lời và context được sinh thực tế theo từng cấu hình. Runner hallucination hiện chấm bản ghi có sẵn. Không dùng chạy lại cùng câu trả lời để tính tác động của thay đổi. Không gộp judge unavailable thành điểm chất lượng 0. Phân biệt lỗi truy xuất với truy xuất thành công nhưng không có kết quả. Baseline thiếu dữ liệu hoặc mất dependency được ghi là chưa đo được.

## Fine-tuning

Chưa xác định được checkpoint fine-tuned trong repo. Trước khi train, dùng lỗi có nhãn trên dev để phân biệt lỗi truy xuất, grounding, format và kiến thức. Prompt, `k`, ngưỡng và rerank là tuning pipeline. Fine-tuning là thay đổi trọng số và cần checkpoint riêng. Chỉ đưa vào thử nghiệm khi xác định được lỗi train nhắm tới, dữ liệu được phép sử dụng và base checkpoint có thể tái lập.

| | Không RAG | Cùng một pipeline RAG |
| --- | --- | --- |
| Base checkpoint | F0 | F1 |
| Fine-tuned checkpoint | F2 | F3 |

F2 − F0 đo fine-tune khi chạy model độc lập. F3 − F1 đo thêm fine-tune khi đã có RAG. F1 − F0 và F3 − F2 đo tác động của RAG ở mỗi checkpoint. Giữ prompt và tham số sinh cố định trong từng cặp. Ghi dataset split, base/adapter digest, cấu hình train và kết quả trên test khóa.

## Kết quả đã đo trong workspace

Cùng hai test hồi quy có tham số, thay lần lượt hai module retrieval bằng code từ `git show d5d1ca4:apps/backend/app/...` trong tiến trình test rồi chạy lại trên workspace. Các client và model đều giả lập.

| Điều kiện | `d5d1ca4` | Workspace full text |
| --- | ---: | ---: |
| Giữ nội dung sau preview qua truy vấn thường, graph retrieve và graph scroll | 0/3 | 3/3 |
| Payload có `text` trống hoặc thiếu vẫn dùng preview | 2/2 | 2/2 |

Đây là phép đo độ đầy đủ của context trên fixture. Chưa có số về độ chính xác model, Recall@k trên corpus thật, tốc độ hoặc chi phí. Ba lượt `eval-nightly` gần nhất đều thất bại. [Lượt kiểm tra gần nhất](https://github.com/23092003e/vas-ifrs-bridge/actions/runs/42315580220) dừng trước khi tải dataset vì thiếu `QDRANT_URL`. Không tìm thấy JSONL trong workspace và Docker Compose không có dịch vụ đang chạy tại thời điểm kiểm tra.

Bước mở khóa phép đo là có corpus/index cố định, bộ câu hỏi gán nhãn và môi trường model/embedding/reranking truy cập được. Chạy A–D trước, lưu kết quả từng câu, rồi bật E riêng với D. Chưa bắt đầu thay đổi pipeline tiếp theo trong lúc thiếu baseline thật.

## Chuẩn bị baseline khi VM Qdrant hết hạn

Qdrant trên VM cũ không còn truy cập được. Kiểm tra local không thấy Docker volume có tên chứa `qdrant` hoặc snapshot được Git theo dõi. Repo có cấu hình Qdrant local tại `infra/docker/docker-compose.qdrant.yml`.

Đã chạy thử `bash skills/vas-ifrs-document-ingestion/scripts/run_ingest.sh --scope shared --dry-run --qdrant-url http://127.0.0.1:6333 --ollama-url http://127.0.0.1:11434`. Parser và chunker xử lý thành công 12 tài liệu, sinh 33 chunk VAS và 537 chunk IFRS. Dry run kết thúc trước embedding và upsert.

Corpus trên đủ để chuẩn bị một benchmark pilot trên index mới. Chốt danh sách tài liệu và checksum, lập câu hỏi gắn nhãn theo đoạn, rồi dựng index baseline cùng phiên bản embedding và Qdrant cho các cấu hình so sánh. Dry run chỉ bao phủ hai collection VAS/IFRS. Benchmark toàn bộ pipeline cần bổ sung hoặc ghi rõ phạm vi của mapping, guidance và tenant. Kết quả trên index mới không đại diện cho index lịch sử khi chưa biết corpus và cấu hình của VM cũ.

Đã soạn [14 câu pilot có đáp án và locator](../ingestion/sources/evaluation/README.md), kiểm tra 26 tiêu đề VAS và khóa checksum của pilot cùng 5 tệp tham chiếu. Đây là dữ liệu dev. Corpus được phép dùng, ánh xạ locator sang chunk và tập test độc lập vẫn cần hoàn tất trước khi chạy baseline.

Đã hoàn thành [baseline VAS local](../ingestion/sources/evaluation/VAS_BENCHMARK.md) với 6 câu holdout nội bộ và model thật. Hybrid đạt Hit@5 6/6 như dense. Toàn văn đưa bằng chứng vào prompt ở 6/6 ca so với 0/6 của preview, nhưng chỉ tăng từ 0 lên 1 câu đúng đầy đủ và tăng p50 từ 6,78 lên 43,99 giây. Giữ kết quả này tách khỏi benchmark đầu cuối của stack triển khai.

Đã chạy [thí nghiệm chọn đoạn 512 token trên tập dev](../ingestion/sources/evaluation/VAS_CONTEXT_DEV.md). Bộ chọn giữ 6/14 dấu hiệu so với 4/14 của prefix cùng ngân sách, nhưng đạt 0/7 câu đúng đầy đủ so với 1/7 của toàn văn. Chưa chọn cấu hình để đưa vào ứng dụng.

Đã chạy [đối chứng đoạn nguồn chuẩn](../ingestion/sources/evaluation/VAS_ORACLE_DEV.md) trên cùng bảy câu dev. Nguồn chứa 14/14 dấu hiệu, Qwen 0,5B với prompt cũ đạt 0/7 và với prompt nhắc điều kiện, ngoại lệ đạt 1/7. Giữ cùng đoạn và prompt cũ, Qwen 1,5B đạt 2/7 về nghiệp vụ, p50 sinh 8,41 giây. Tăng trần từ 80 lên 160 token giữ nguyên 2/7 và tăng p50 lên 16,54 giây. Chưa chọn thay đổi mặc định hoặc dùng holdout.

Đã chạy [Qwen 14B qua Ollama local](../ingestion/sources/evaluation/VAS_QWEN14B.md) trên oracle, RAG dev và holdout. Oracle đạt 4/7 với cả hai prompt. Trên holdout, model độc lập đạt 3/6, toàn văn và chọn đoạn 512 đều đạt 5/6 đúng nghiệp vụ. Toàn văn có 5/6 câu đúng đủ dấu hiệu, chọn đoạn có 4/6. p50 giảm từ 38,11 giây xuống 17,39 giây khi chọn đoạn. Chưa đổi mặc định dựa trên tập nhỏ này.

Đã dựng stack local riêng và đo qua [FastAPI SSE](../ingestion/sources/evaluation/VAS_API_BENCHMARK.md) với bge-m3, Qdrant, BM25, TEI, Qwen 14B và Postgres. Lượt smoke cho thấy rerank mặc định chạm timeout 15 giây. Cặp so sánh dùng cùng giới hạn rerank giảm và đo context toàn văn với bộ chọn đoạn 512/1.024 token. Số đo chỉ áp dụng cho QA VAS tiếng Việt trên stack thử nghiệm.

Cả 26 lượt so sánh có điểm TEI và lưu được câu trả lời. Trên dev, toàn văn đạt 3/7 câu đúng, bộ chọn đạt 2/7. Trên holdout mới, cả hai đạt 4/6, bộ chọn giảm độ trễ tổng p50 từ 65,52 xuống 41,98 giây, nhưng giữ 8/11 dấu hiệu trong prompt so với 10/11 của toàn văn. Giữ toàn văn trong đường chạy ứng dụng. Graph không bổ sung đoạn nguồn trên bộ câu hỏi này. Chấm độc lập, benchmark IFRS và fine-tuning còn mở.

Đã đo riêng [reranker](../ingestion/sources/evaluation/VAS_RERANK_BENCHMARK.md). Trên cùng ứng viên dev, RRF top 8 giữ 12/14 dấu hiệu so với 6/14 khi áp ngưỡng TEI. Chạy SSE RRF trên dev đạt 3/7 như mốc TEI, nhưng không phát được citation và sáu prompt vượt cửa sổ model. Giữ chính sách reranker trong ứng dụng. Đã sửa thứ tự mở rộng ontology và xác nhận với ba hash seed cùng 122 unit test. Thứ tự kết quả truy xuất thật vẫn có biến động.

Đã chạy [so sánh context toàn văn và giới hạn 3.000 token trên cùng top 8 RRF](../ingestion/sources/evaluation/VAS_RRF_CONTEXT_BUDGET.md). Cả 26 lượt SSE đều lưu được phản hồi. Số câu đúng tăng từ 2/7 lên 5/7 trên dev và từ 0/6 lên 4/6 trên bộ sáu câu đã khóa. P50 tổng tăng từ 52,72 lên 61,63 giây trên dev và từ 46,00 lên 55,39 giây trên bộ sáu câu. Giữ giới hạn context trong runner để đối chiếu với TEI hiện tại trên tập mới.

Đã thử một thay đổi cuối trong [prompt nêu kết luận trước](../ingestion/sources/evaluation/VAS_CONCLUSION_FIRST.md). Hai nhánh đạt 2/5 câu đúng. Prompt mới tăng số câu phát citation từ 2/5 lên 5/5 nhưng giảm số câu vừa đúng vừa đủ dấu hiệu trong các đoạn trích từ 1/5 xuống 0/5. Giữ prompt hiện tại trong ứng dụng.

Đã chạy [xác nhận hai pipeline trên 24 câu VAS mới](../ingestion/sources/evaluation/VAS_CONFIRMATION.md). Cả 48 lượt SSE hoàn tất và lưu được. RRF giới hạn 3.000 token đạt 15/24 câu đúng, pipeline hiện tại đạt 4/24 và có 24/24 lượt TEI timeout. RRF có năm lỗi nghiêm trọng mới trên các câu mà baseline không bị chấm lỗi nghiêm trọng. Giữ cấu hình ứng dụng. Kết quả là chấm nội bộ ẩn tên nhánh, chưa có chuyên gia độc lập xác nhận.

## Hồi quy Chat và Compare

Trước sửa, bộ test tập trung tái hiện năm lỗi gồm marker citation trong nhóm, hai ca retry QA và hai ca truy xuất thất bại toàn bộ. Sau sửa, cả 129 unit test backend qua. Bộ lọc chỉ xử lý các marker đứng riêng hoặc nhóm phân cách bằng dấu phẩy hay khoảng trắng, theo cú pháp hai giao diện nhận diện. QA kiểm tra lại nội dung sinh ở lần retry và giữ bản đầu đã lọc nếu retry rỗng. Chat và Compare trả SSE `error` với thông báo cố định khi mất toàn bộ truy xuất và không có nguồn dự phòng. Compare bật hành vi nghiêm ngặt tại chỗ gọi retriever để giữ hợp đồng của các agent đang dùng retrieval bổ sung.

Sáu ca smoke qua HTTP localhost đều qua với Postgres thật, auth thử nghiệm, truy xuất và LLM mô phỏng. Hai luồng đều trả lời nếu còn nguồn, xử lý kết quả rỗng và phát lỗi riêng nếu mọi truy xuất thất bại. `final` và citation khớp nội dung lịch sử khi có câu trả lời. Khi mất toàn bộ truy xuất, lịch sử chứa câu hỏi mà không có bản ghi assistant. Lượt này đo tính đúng của luồng và khóa citation, chưa đo trích dẫn có thực sự hỗ trợ nhận định, chất lượng model hoặc giao diện đăng nhập.

## CORS, phiên đăng nhập và cách ly tenant

Trước sửa, preflight với origin được phép và origin ngoài danh sách đều nhận `401`, còn GET thiếu token từ origin được phép không có header CORS. Đưa CORS ra ngoài AuthMiddleware và giữ tracing, metrics ở ngoài CORS. Sau sửa, preflight hợp lệ nhận `200`, origin ngoài danh sách nhận `400` và GET thiếu token vẫn `401` kèm header CORS đúng. Cả 132 unit test backend và 31 test frontend qua.

Trên Supabase local tách biệt, bộ RLS thất bại trước sửa khi trigger đăng ký gọi `public.uuid_generate_v4()` nhưng `uuid-ossp` của Supabase nằm ở schema `extensions`. Migration `0008` chuyển sang `pg_catalog.gen_random_uuid()`. Bộ RLS chạy qua sau sửa. Hai tài khoản đăng ký qua GoTrue nhận JWT thật, có tenant khác nhau, chỉ thấy tài liệu của mình qua PostgREST và hội thoại của mình qua FastAPI. Header tenant sai nhận `403`. Viewer nhận `403` ở route admin, còn owner qua RBAC và nhận `501` từ route chưa triển khai.

Playwright xác minh riêng hai phiên trình duyệt. Cả hai được chuyển hướng tới login khi chưa có phiên, đăng nhập bằng mật khẩu, giữ phiên khi tải lại, nhận `404` khi thử đọc hội thoại tenant kia qua Next.js và nhận `401` sau đăng xuất. Supabase và database hội thoại đều là môi trường thử nghiệm local. Migration chưa được áp dụng lên môi trường triển khai.

## Baseline ingestion và retry

Gửi tài liệu `.txt` giả qua API FastAPI in-process với Postgres, bge-m3 qua Ollama, BM25 và Qdrant local. Tài liệu chuyển sang `ready` và truy xuất hybrid trả đúng nội dung trong collection tenant. Chạy lại job với cùng document ID và cùng nội dung giữ nguyên một điểm Qdrant. Ca này chưa đo tải lên cùng tệp thành hai document ID hoặc nhiều worker đồng thời.

Trước sửa, UI và API cho tải `.xls` qua dù parser Excel chỉ hỗ trợ `.xlsx`. Đã bỏ `.xls` khỏi kiểm tra định dạng và bộ chọn tệp. API trả `415` và frontend báo không hỗ trợ. Khi dừng riêng tiến trình thử nghiệm giữa lúc embedding, bản ghi vẫn ở `processing`. Một lần chạy lại trực tiếp job sau lỗi embedding mô phỏng đã đưa tài liệu về `ready`. Trước sửa, lần chạy thành công còn để `error_message` cũ. Sau sửa, lỗi cũ được xóa. Chưa có tự động nhận lại job sau restart. Cả 133 unit test backend và 32 test frontend qua.

### Khôi phục sau restart

Backend quét tài liệu `pending` và `processing` lúc khởi động và mỗi 30 giây. Job có tệp nguồn đọc được mới được nhận lại. Mỗi job giữ khóa tư vấn PostgreSQL theo document ID trên cùng một phiên DB. Nếu một tiến trình khác đang giữ khóa, lượt quét bỏ qua; khi tiến trình chết, PostgreSQL tự nhả khóa. Qdrant xác nhận đã ghi điểm trước khi trạng thái chuyển sang `ready`.

Đã dừng tiến trình riêng bằng SIGKILL trong hai ca, giữa embedding và sau khi Qdrant ghi điểm nhưng trước khi Postgres nhận `ready`. Khi job còn sống, lượt quét bỏ qua đúng job. Sau khi khởi động lại qua FastAPI lifespan, cả hai bản ghi tự về `ready`, mỗi tài liệu có đúng một điểm Qdrant. Lượt quét sau đó giữ nguyên kết quả. Cả 134 unit test backend qua. Phép đo dùng Postgres, Ollama và Qdrant local, cùng tệp nguồn trên đĩa còn tồn tại sau restart. Backend cần kết nối Postgres trực tiếp hoặc pool giữ phiên và đĩa bền vững có chứa tệp nguồn; chưa kiểm chứng triển khai nhiều máy hoặc volume tạm.

## RAG song ngữ và độ tin cậy của luồng SSE

Với Chat và Compare, kết nối đóng trước `final` giờ được báo là luồng chưa hoàn tất. Nhấn dừng bỏ nội dung đang sinh và proxy chuyển tín hiệu hủy tới upstream. Compare có thể dừng ngay trong lúc xử lý và cho thử lại sau lỗi provider. Với kết quả truy xuất rỗng, backend trả thông báo thiếu nguồn theo ngôn ngữ yêu cầu mà không gọi model. Đây là kiểm tra tập nguồn rỗng, chưa xác nhận độ bao phủ nguồn cho trường hợp Compare chỉ có một phía chuẩn mực.

Sáu ca HTTP SSE trên FastAPI và Postgres local đều qua, gồm nguồn rỗng, provider lỗi và đóng kết nối sau token đầu ở mỗi luồng. Các ca hủy và lỗi không lưu bản nháp assistant; ca nguồn rỗng lưu đúng nội dung cuối. Provider và kết quả truy xuất dùng fixture. Playwright qua Supabase/Next.js thật xác minh tải lại lịch sử từ Postgres. Các ca EOF, nút dừng, lỗi và thử lại dùng phản hồi SSE dựng sẵn trong trình duyệt. Tổng cộng 136 unit test backend và 35 test frontend qua. TypeScript check qua.

Chạy sáu lượt QA qua FastAPI SSE với cùng ba tình huống VAS ở hai ngôn ngữ. Dùng Qwen 14B, chỉ mục VAS tiếng Việt, RRF top 8, context tối đa 3.000 token nội dung nguồn và trần 160 token đầu ra. Các cặp dùng cùng nhãn nghiệp vụ và các dấu hiệu nguồn đã khóa; assistant dịch câu hỏi và chấm kết quả. Cả sáu phản hồi được lưu.

| Thước đo | Tiếng Việt | Tiếng Anh |
| --- | ---: | ---: |
| Đúng nghiệp vụ | 3/3 | 2/3 |
| Dấu hiệu bằng chứng trong prompt | 6/6 | 4/6 |
| Dấu hiệu trong đoạn đã trích | 3/6 | 4/6 |
| Độ trễ tổng p50 | 51,65 s | 51,13 s |

Cả hai ngôn ngữ trả lời đúng về phân bổ chi phí theo công suất và hàng vượt nhu cầu hợp đồng. Ở câu cổ tức, lượt tiếng Anh thiếu cả hai dấu hiệu trong context và trả lời sai về ghi nhận nợ cuối kỳ. Lượt tiếng Việt trả lời đúng nhưng đoạn được trích không có dấu hiệu tương ứng. Ba cặp chỉ đủ để xác nhận ca sai này, chưa đủ để kết luận chất lượng song ngữ nói chung. Lượt này chưa dùng corpus IFRS để chấm nghiệp vụ Compare.

[Bộ câu song ngữ](../ingestion/sources/evaluation/vas-bilingual-v1.jsonl) · [Bản ghi sáu lượt](../ingestion/sources/evaluation/vas-bilingual-v1.results.json)

## Bộ đọc Trial Balance

Trước sửa, 2/12 ca parser qua. Trong mẫu thử, bộ đọc lấy 1.250 ở cột dư Nợ đầu kỳ cho cả `debit` và `balance`, trong khi phát sinh Nợ là 8.450, phát sinh Có là 8.100 và dư Nợ cuối kỳ là 1.600. Bộ đọc cũ cũng có thể chọn nhầm tên tài khoản làm mã và diễn giải `1,23` thành `123`.

Sau sửa, 12/12 ca parser và 146/146 unit test backend qua. Với Trial Balance đủ cột, parser giữ cả sáu số liệu đầu kỳ, phát sinh và cuối kỳ. Hai trường `debit` và `credit` lấy số phát sinh, còn `balance` bằng dư Nợ cuối kỳ trừ dư Có cuối kỳ. CSV và XLSX đều giữ số 0 ở đầu mã tài khoản lưu dạng văn bản. Bộ đọc kiểm tra tên cột, từ chối cột trùng hoặc bộ cột kỳ thiếu, và chỉ chấp nhận dấu phẩy phân nhóm hàng nghìn trong chuỗi số tiền.

Chạy lại CSV dựng trực tiếp từ template frontend qua công cụ `parse_gl_file`. Cả 8/8 dòng khớp mã, tên, sáu số liệu gốc và ba giá trị chuẩn hóa. Route upload GL HTTP vẫn trả `501`, nên kết quả này xác minh parser và công cụ gọi parser.

## Mapping, bút toán và báo cáo GL

Baseline có 146 unit test qua. Bổ sung bốn ca kiểm tra bút toán cho kết quả 4/8 trước sửa và 8/8 sau sửa. Các ca tái hiện giá trị vô hạn, thiếu tài khoản, chênh lệch bị làm tròn mất và mất phân bổ nhiều dòng. Sau sửa, parser bút toán giữ từng dòng và cộng Decimal chính xác đến hai chữ số thập phân.

Mapping ưu tiên quy tắc do tenant duy trì, sau đó tra danh mục tài khoản VAS sẵn có. Mã chưa có quy tắc được đánh dấu để người dùng xử lý. Các route upload, mapping, bút toán và báo cáo chuyển từ stub sang thao tác trên Postgres. Tệp upload được đọc tạm thời, sau đó giữ số liệu chuẩn hóa và checksum trong Postgres. Khi tạo bút toán, người dùng chọn mã nguồn đã ánh xạ và nhập diễn giải cùng các dòng định khoản. Phê duyệt xác thực lại số và lưu người duyệt, thời điểm duyệt. Bản nháp từ chối được giữ để truy vết. Báo cáo lưu bản chụp và chỉ cộng các bút toán đã duyệt.

Test tích hợp trên PostgreSQL với hai tenant kiểm tra cô lập quy tắc, quyền đọc và ghi, gửi lại upload và phê duyệt đồng thời, khóa báo cáo khi còn bản nháp, từ chối bản nháp và tải CSV. Fixture ban đầu có tiền mặt 100 và phải trả -100. Sau khi duyệt Có tiền mặt 0,30, Nợ A 0,10 và Nợ B 0,20, số dư lần lượt là 99,70, -100, 0,10 và 0,20. Tổng điều chỉnh bằng 0 và nhật ký ghi nhận thao tác.

Chromium đi qua đăng nhập Supabase, upload CSV, bổ sung quy tắc, ghi bút toán, duyệt, tạo báo cáo và tải CSV. Sau khi dừng và khởi động lại FastAPI, phiên trình duyệt đọc lại bản chụp và tải cùng số dư 99,70. Đầu ra là bảng cân đối phát sinh sau điều chỉnh. Báo cáo tài chính IFRS đầy đủ và các phép tính IFRS 16, ECL, thuế hoãn lại cần thêm dữ liệu nghiệp vụ và rà soát riêng.

## CI và vận hành

Backend CI có PostgreSQL 15 riêng, chạy upgrade, downgrade về `0002`, upgrade lại rồi kiểm tra luồng GL. Frontend CI cài từ lockfile và chạy production build. Docker Compose dev chạy Alembic trước Uvicorn. Kustomize staging và production render thành công, có kiểm tra readiness và giới hạn upload ở ingress. Terraform qua `fmt` và `validate` sau khi tải provider đã khóa. Kiểm tra cục bộ gồm 150 unit test backend, 35 test frontend, 6 test handler Supabase cùng bộ RLS, 2 test n8n MCP và 6 test Qdrant MCP.

Audit npm trước sửa báo 5 cảnh báo dependency production, gồm 1 critical. Nâng Next.js từ `15.5.21` lên `15.5.29` và cập nhật các dependency gián tiếp liên quan. Sau đó cập nhật Vitest lên `4.1.12` cùng Vite và esbuild để xử lý các cảnh báo ở bộ kiểm thử. Audit đầy đủ trên lockfile npm và pnpm đều báo 0 cảnh báo. Cả hai image Docker build thành công trên lockfile cuối, và Chromium đã kiểm chứng luồng GL với Next.js `15.5.29`.

Đã kiểm chứng upgrade sạch và vòng downgrade/upgrade trên database thử nghiệm. Việc hạ migration `0003` xóa dữ liệu mới của luồng GL, vì vậy vòng này chỉ được chạy trên database thử nghiệm. Chưa chạy release GitHub Actions hoặc triển khai lên staging/production. MCP được xác minh bằng bộ test dự án. Workflow n8n và dịch vụ Qdrant từ xa cần một lượt kiểm tra trên môi trường triển khai.

## Pilot VAS–IFRS với LoRA

Đã khóa 64 câu train giả lập, 16 câu dev ở nhóm chủ đề khác và 20 câu test VAS–IFRS. Dùng Qwen2.5-1.5B-Instruct, chạy baseline rồi train LoRA và chạy đủ bốn cấu hình cùng tập test. Với mô hình gốc, thêm RAG tăng từ 11/20 lên 15/20. Trên cùng RAG, LoRA tăng từ 15/20 lên 17/20 và tăng p50 từ 0,531 lên 0,760 giây. Tỷ lệ đúng kèm đủ bằng chứng của cấu hình kết hợp là 4/20. Dữ liệu train là tình huống giả lập, corpus RAG là 18 thẻ tự soạn có định vị nguồn, và nhãn test chưa được người chấm độc lập xác nhận. [Kết quả, adapter và cách tái lập](../ingestion/sources/evaluation/matrix-v1/README.md)

## Compare có trích dẫn theo từng phía

Đã tách truy xuất VAS khỏi IFRS/IAS, giữ lọc tenant, kiểm tra mã trích dẫn từng nhận định và trả thông báo khi thiếu nguồn. Trên bốn câu tự do khóa sau khi hoàn thiện bộ kiểm tra, cả hai cấu hình đều có đủ thẻ cần thiết trong ngữ cảnh. Câu trả lời đúng kèm đủ bằng chứng tăng từ 0/4 lên 2/4, độ trễ p50 giảm từ 15,90 xuống 5,01 giây. Hai câu còn lại dừng vì model không phát mã trích dẫn hợp lệ. Benchmark dùng cùng Qwen 1,5B gốc với chỉ mục thẻ cục bộ và assistant chấm nội dung. [Kết quả từng câu](../ingestion/sources/evaluation/compare-v2/README.md)

## Kiểm chứng ngữ nghĩa Compare trên 24 câu tự do

Trong 20 câu trả lời được, Compare lấy đủ hai nguồn ở 20/20 câu và dẫn đủ hai mã kỳ vọng ở 14/20, nhưng chỉ 4/20 vừa đúng nghiệp vụ vừa đủ bằng chứng. Có 5 lỗi nghiệp vụ trọng yếu dù mã trích dẫn hợp lệ. P50 local là 7,59 giây. Bốn ca thiếu nguồn tránh kết luận về chuẩn vắng nguồn, trong đó ba ca đạt yêu cầu đầy đủ. Chưa đưa vào staging và chưa fine-tune thêm. Ưu tiên đánh giá sự hỗ trợ của từng đoạn đối với nhận định trước khi tổng hợp. [Báo cáo và chấm từng câu](../ingestion/sources/evaluation/compare-v3/README.md)

## Đối chứng bộ kiểm tra nhận định Compare

Chẩn đoán offline bằng Qwen 1,5B chặn 2/5 nhận định lỗi và chặn nhầm 5/10 nhận định đúng đã biết. Trên 16 câu mới, hai nhánh dùng chung bản sinh. Trong 12 câu đủ nguồn, bộ kiểm tra giảm lỗi nghiệp vụ trọng yếu từ 2 xuống 1 nhưng cũng giảm câu đúng có đủ nguồn từ 3 xuống 2. P50 tăng từ 7,75 lên 8,82 giây và số câu từ chối dù đủ nguồn tăng từ 2 lên 3. Cả hai nhánh xử lý an toàn 4/4 ca thiếu nguồn, đạt đầy đủ 2/4. Kết quả không đạt tiêu chí staging đã khóa. Bộ kiểm tra chỉ chạy offline. [Báo cáo đối chứng và dữ liệu](../ingestion/sources/evaluation/compare-v4/README.md)

## Compare ở chế độ trích đoạn

Đã thêm `COMPARE_MODE=evidence` để đối chiếu trực tiếp đoạn nguồn, giữ citation và thông báo thiếu chuẩn mực. Hai nhánh dẫn đủ hai đoạn ở 6/6 câu có nguồn. Chế độ tổng hợp có một lỗi nghiệp vụ và chế độ trích đoạn không sinh thêm kết luận sai. Cả hai chỉ trả lời trực tiếp đủ ý ở 1/6 theo rubric. P50 local giảm từ 8,06 giây xuống 13 ms khi bỏ sinh model, đo trong cùng harness với 18 thẻ. Giữ chế độ trích đoạn opt-in để rà nguồn. Chưa triển khai staging. [Báo cáo và điểm từng câu](../ingestion/sources/evaluation/compare-v5/README.md)
