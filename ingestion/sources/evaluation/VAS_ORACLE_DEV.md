# Đối chứng đoạn nguồn chuẩn trên VAS dev

## Kết quả

| Cấu hình | Câu đủ dấu hiệu nguồn | Dấu hiệu trong prompt | Đúng đầy đủ | Token đầu vào trung vị |
| --- | ---: | ---: | ---: | ---: |
| Chọn đoạn 512, prompt cũ | 2/7 | 6/14 | 0/7 | 584 |
| Toàn văn top 5, prompt cũ | 5/7 | 9/14 | 1/7 | 2.509 |
| Đoạn nguồn chuẩn, prompt cũ | 7/7 | 14/14 | 0/7 | 235 |
| Đoạn nguồn chuẩn, prompt nhắc điều kiện và ngoại lệ | 7/7 | 14/14 | 1/7 | 269 |

Đưa đúng đoạn chuẩn bổ sung toàn bộ dấu hiệu còn thiếu nhưng không làm tăng số câu đúng đầy đủ với prompt cũ. Con số oracle thấp hơn toàn văn top 5 trên mẫu này vì hai prompt có phần context khác nhau, và đoạn nguồn chuẩn là một điều kiện chẩn đoán chứ không phải trần điểm. Qwen 0,5B vẫn mắc lỗi đọc nguồn. Cả hai prompt đưa đúng kỳ áp dụng Thông tư 99 nhưng bỏ ngoại lệ chuyển tiếp về cổ phần hóa theo Thông tư 200. Prompt nhắc ngoại lệ lại thành công ở câu từ chối tính dự phòng khi thiếu dữ liệu, nhưng chưa đủ để chọn làm mặc định.

Cả hai prompt oracle nêu đúng hai nội dung phải công bố cho sự kiện không điều chỉnh trọng yếu. Rubric cũ cũng yêu cầu nói rõ không điều chỉnh số liệu, nên cả hai bị chấm thiếu ý ở câu đó. Nếu chỉ chấm các nội dung công bố mà câu hỏi trực tiếp hỏi, oracle sẽ đạt 1/7 với prompt cũ và 2/7 với prompt mới. Kết luận rằng nhiều lỗi vẫn xảy ra dù có nguồn không đổi.

Độ trễ sinh p50 của hai cấu hình oracle lần lượt là 2,62 s và 3,05 s. Các số này không gồm retrieval. Đo trên CPU với bảy câu dev, không so trực tiếp với độ trễ đầu cuối của ứng dụng. Chưa rà soát điểm độc lập và chưa dùng holdout để chọn cấu hình.

[Kết quả từng lượt và đoạn nguồn](vas-oracle-dev-v1.json) · [Điểm và lý do từng câu](vas-oracle-dev-v1.grades.json).

Kết quả xác nhận hai vấn đề riêng. Bộ truy xuất hoặc bộ chọn bỏ sót bằng chứng trong một số câu, và model vẫn dùng sai hoặc bỏ qua những đoạn được cung cấp. Cần model sử dụng nguồn đủ tốt trước khi chọn cách nén context trên dev và kiểm tra trên holdout.

## Đối chứng checkpoint và giới hạn đầu ra

Đã chạy [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Cùng bảy câu, đoạn nguồn, prompt gốc và CPU bốn luồng. Đã đối chiếu từng chuỗi ID token đầu vào giữa hai tokenizer và xác nhận hoàn toàn giống nhau. Giữ giải mã greedy. Sau lượt so checkpoint với 80 token, thử riêng giới hạn 160 token trên cùng checkpoint 1,5B.

| Checkpoint | Trần token đầu ra | Đúng đầy đủ về nghiệp vụ | Chạm trần | p50 sinh |
| --- | ---: | ---: | ---: | ---: |
| Qwen 0,5B | 80 | 0/7 | 4/7 | 2,62 s |
| Qwen 1,5B | 80 | 2/7 | 5/7 | 8,41 s |
| Qwen 1,5B | 160 | 2/7 | 2/7 | 16,54 s |

1,5B trả lời đúng hai nội dung nghiệp vụ mà 0,5B bỏ lỡ, gồm đo lường hàng tồn kho và xử lý sự kiện cần điều chỉnh. Câu hàng tồn kho vẫn có một cách diễn giải tên VAS do model tự đặt. Điểm 2/7 chỉ tính đúng nghiệp vụ; nếu loại mọi lỗi thực tế dù ngoài yêu cầu, câu này cũng không đạt. Lượt 160 giữ nguyên phần đầu của câu trả lời ở cả bảy ca và không khôi phục thêm ca đúng đầy đủ. Ca lập dự phòng theo từng mặt hàng trả lời sai trong 20 token, nên tăng trần không xử lý được lỗi đó. Hai ca còn chạm trần ở 160 chưa cho biết kết luận nếu tiếp tục sinh.

[Lượt 80 token](vas-oracle-qwen15b-dev-v1.json) · [Điểm 80 token](vas-oracle-qwen15b-dev-v1.grades.json) · [Lượt 160 token](vas-oracle-qwen15b-cap160-dev-v1.json) · [Điểm 160 token](vas-oracle-qwen15b-cap160-dev-v1.grades.json).

Tái lập hai lượt bằng `run_vas_oracle.py` với `--base-only --model Qwen/Qwen2.5-1.5B-Instruct --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 --max-new-tokens 80` hoặc `160`, và `--out` khác cho mỗi lượt. Chưa chọn checkpoint hoặc trần mới để triển khai. Trước khi dùng holdout, có thể thử prompt ép trả lời ngắn và nêu kết luận trước trên 1,5B, hoặc đo model dự kiến triển khai khi runtime sẵn sàng.

## Thiết kế

Mục tiêu là tách lỗi truy xuất và chọn đoạn khỏi lỗi đọc bằng chứng. Bảy câu giữ nguyên từ lần [đo context 512 token](VAS_CONTEXT_DEV.md). Runner cắt nguyên văn các đoạn đã định vị từ ba tệp VAS. Nó kiểm tra SHA-256 của bộ câu hỏi, nhãn và tài liệu đối chiếu với lần đo cũ. Cả 14 dấu hiệu phải xuất hiện trước khi bắt đầu sinh câu trả lời. Các đoạn nguồn không chứa đáp án do trợ lý soạn.

Đo hai cấu hình trên cùng các đoạn nguồn. `oracle_base` giữ nguyên prompt hệ thống, checkpoint Qwen 0,5B, CPU, giải mã greedy và giới hạn 80 token đầu ra. `oracle_evidence_prompt` giữ các điều kiện đó và chỉ bổ sung hướng dẫn nêu kết luận, điều kiện hoặc ngoại lệ, và dữ liệu còn thiếu. Thứ tự hai cấu hình được đảo xen kẽ qua các câu. Mốc top 5 và mốc chọn đoạn 512 lấy từ lần đo đã lưu trên cùng các câu.

Chấm đúng đầy đủ khi câu trả lời đáp ứng các ý bắt buộc và không có mâu thuẫn quan trọng. Kết quả oracle là phép chẩn đoán trên đoạn do người chọn sẵn. Nó không cho biết bộ truy xuất đã có thể chọn đoạn tương đương hay chưa. Các so sánh độ trễ của oracle chỉ tính sinh câu trả lời, vì phép đối chứng bỏ qua truy xuất.

```sh
HF_HOME=/private/tmp/vas-benchmark-hf HF_HUB_OFFLINE=1 PYTHONPATH=apps/backend \
  apps/backend/.venv/bin/python ingestion/sources/evaluation/run_vas_oracle.py
```

Thêm `--verify-only` để chỉ kiểm tra nguồn, không tải model hoặc sinh câu trả lời.
