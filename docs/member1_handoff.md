# Bàn giao Member 1 — Knowledge Base & Data Governance

Member 1 cung cấp dữ liệu và công cụ tái tạo cho UC-02. Bộ bàn giao gồm:

| Phần việc | Sản phẩm | Người nhận |
| --- | --- | --- |
| RAG Band Descriptors | 72 chunks, đúng 6 metadata; PDF nguồn và script rebuild ChromaDB | Member 2 |
| Corpus đối chiếu đạo văn | 1.800 bài public: 600 Task 1, 1.200 Task 2 | Member 4 |
| Benchmark chấm Writing | 84 bài, 69 dev / 15 test, đủ 4 tiêu chí và overall; ảnh đề Task 1 | Member 5 |
| Basic cases | 5 nhóm / 6 bài, `scores=null`, có kết quả mong đợi | Member 5 |
| Nguồn và phương pháp nhãn | URL từng bài, phương pháp lấy điểm nguồn, hướng dẫn sử dụng | Cả nhóm |

## Đọc theo thứ tự

1. [Nguồn dữ liệu](data_sources.md).
2. [Bàn giao Member 2](member1_to_member2_handoff.md): descriptors và ChromaDB.
3. [Bàn giao Member 4](member1_to_member4_handoff.md): schema corpus và thay đổi loader cần thực hiện.
4. [Bàn giao Member 5](member1_to_member5_handoff.md): benchmark, ảnh, basic cases và cách tách đáp án khỏi Agent.
5. [Chi tiết benchmark](../evals/README.md) và [xem ảnh Task 1](../evals/materials/README.md).

## Kiểm tra sau khi clone

Từ thư mục gốc repository:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -B scripts/check_member1_data.py
.venv/Scripts/python.exe -B scripts/check_writing_benchmark.py
```

Các kiểm tra dữ liệu không gọi LLM và không yêu cầu API key. JSON, corpus và ảnh public có sẵn trong nhánh; không cần copy cache từ máy người chuẩn bị. `data/chroma_db/` không nằm trên Git: tạo DB theo hướng dẫn Member 2 khi cần retrieval.

## Phạm vi bàn giao

- Descriptors, corpus và benchmark là ba nguồn riêng; không đưa bài benchmark/corpus vào collection descriptors hoặc ngân hàng đề sản phẩm.
- Benchmark giữ nguyên 84 bài, điểm công bố và cách chia dev/test. Không dùng LLM để tạo điểm chuẩn mới.
- Nguồn public được tiếp nhận theo quy định cập nhật; không bắt buộc trường `license` hoặc danh tính thật người viết/người chấm.
- Schema Member 1 được giữ như bộ dữ liệu đã chốt. Những điều chỉnh loader, DTO, runner và luồng ảnh thuộc Member 4/5 được chỉ rõ trong handoff; PR dữ liệu không thay code Agent/UI của họ.
- Kiểm tra cấu trúc và smoke test dữ liệu không thay cho đánh giá mô hình. Kết quả mock không được báo cáo như độ chính xác chấm band hoặc tỷ lệ phát hiện đạo văn thực tế.

## Kết quả kiểm tra bộ bàn giao

- 24 tests Member 1 pass; lint và kiểm tra file/secrets trong index pass.
- Toàn suite hiện 300 pass, 1 fail: runner Member 5 chưa ánh xạ `case_id` của basic cases sang ID nội bộ. [Handoff Member 5](member1_to_member5_handoff.md) ghi cách điều chỉnh; PR dữ liệu không sửa runner hoặc các test thuộc phần đó.
