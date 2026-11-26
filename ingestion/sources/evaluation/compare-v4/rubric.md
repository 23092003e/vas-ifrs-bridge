# Thiết kế phép đối chứng đã chốt trước khi chạy

Bước chẩn đoán dùng 5 nhận định lỗi đã ghi ở Compare v3 và 10 nhận định được nguồn hỗ trợ. Số thứ tự trong controls tính theo đoạn của bản final, bắt đầu từ 1. Nhận định đưa ra kết luận trái nguồn là mâu thuẫn. Nhận định thêm quan hệ không có trong đoạn là thiếu bằng chứng. Cả hai loại đều bị chặn.

Tập chính có 12 câu đủ nguồn và 4 ca thiếu chuẩn mực. Mỗi câu chỉ sinh một bản với agent Compare hiện tại. Nhánh đối chứng trả bản final nguyên trạng, nhánh thử nghiệm kiểm tra và có thể bỏ từng nhận định trong chính bản final đó. Bộ kiểm tra chỉ đọc câu hỏi, nhận định và các đoạn mà nhận định đã dẫn. Chỉ giữ nhận định được hỗ trợ toàn bộ. Giữ nguyên cảnh báo thiếu nguồn. Một câu đầy đủ phải đúng nghiệp vụ, có các ý bắt buộc, có đủ hai hướng bằng chứng với câu đối chiếu và không có nhận định sai trọng yếu. Với ca thiếu nguồn, không được kết luận về chuẩn vắng nguồn và phải trả phần có căn cứ nếu còn nguồn. Ca không còn nguồn nào cần từ chối toàn bộ.

Ghi số câu sai lọt qua, số câu đúng có đủ nguồn, số câu bị từ chối toàn bộ, số câu thiếu nguồn xử lý an toàn và p50. Thời gian phương án thử gồm thời gian sinh Compare đã đo cộng thời gian kiểm tra của từng câu. Bỏ thời gian nạp model ở cả hai nhánh. Chấm nội dung thủ công, theo cùng rubric cho hai nhánh.

Chỉ đề xuất thử nghiệm staging có người rà soát khi lỗi trọng yếu giảm, không còn lỗi trọng yếu trong mẫu, nhánh kiểm tra giữ số câu đạt so với đối chứng, ít nhất 7/12 câu đủ nguồn đạt và cả bốn ca thiếu nguồn xử lý an toàn. Mức đa số kế thừa tiêu chí của Compare v3.
