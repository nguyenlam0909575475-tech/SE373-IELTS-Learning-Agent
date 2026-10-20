# Minh bạch sử dụng AI

Thành viên 2 dùng Codex để hỗ trợ đọc phân công/handoff; viết tool retrieval,
adapter DTO/lỗi, skill writing-assessment, bộ đo Precision/Recall/MRR, test và
tài liệu hướng dẫn. Các truy vấn relevance và nhãn band trong
`evals/data/retrieval_queries.json` được AI hỗ trợ soạn, chưa được thành viên
khác kiểm tra độc lập; cần giữ trạng thái này khi báo cáo kết quả.

Test dùng fixture giả lập để kiểm tra hợp đồng, metadata filters và các lỗi;
fixture không phải bài có điểm chuẩn IELTS. Các phép đo thật phải được chạy
trên index tái tạo từ nguồn chính thức và lưu kết quả thực tế. Không dùng AI
gán điểm chuẩn cho benchmark Writing; không tạo dữ liệu người học thật.

Thành viên cần đọc, chạy lại và giải thích được code trước khi nộp/vấn đáp.
Việc khai báo AI không thay cho kiểm tra chéo dữ liệu hoặc nghiệm thu tích hợp.
Phần AI hỗ trợ thành viên 1 được ghi trong tài liệu bàn giao của thành viên 1.
