# Member 1 → Member 2: Band Descriptors và ChromaDB

## Dữ liệu nhận bàn giao

- `ielts-writing-band-descriptors.pdf`: nguồn chính thức [IELTS.org, May 2023](https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf).
- `data/processed/writing_descriptors.json`: 72 chunks; mỗi chunk là một ô Task × tiêu chí × band 1–9.
- `data/processed/descriptor_provenance.json`: trang và tọa độ ô nguồn, hai policy Band 0 riêng.
- `scripts/rebuild_vectorstore.py`: tạo lại collection `writing_descriptors`; ChromaDB không nằm trên Git.

Mỗi chunk gồm `text` và đúng 6 metadata: `chunk_id`, `test_part`, `criterion`, `band`, `version`, `source_url`. Task 1 dùng `task_achievement`, Task 2 dùng `task_response`; ba tiêu chí còn lại là `coherence_cohesion`, `lexical_resource`, `grammatical_range_accuracy`. `test_part` chỉ là `task1` hoặc `task2`.

Version là `ielts_writing_2023_05`; ID ổn định dạng `writing_task1_task_achievement_b6_2023_05`. Không tự nội suy descriptor nửa band. Nguồn có điều khoản gắn nhãn General Training trong một số ô; chỉ áp dụng phần Academic của đề tài.

## Tạo DB sau khi clone

Chạy từ gốc repository:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -B scripts/check_member1_data.py
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py --validate-only
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py
```

JSON đã có sẵn để rebuild; không cần tải lại PDF mỗi lần. Chroma có thể tải model `all-MiniLM-L6-v2` ở lần đầu, cần mạng nhưng không cần API key. DB sinh ở `data/chroma_db/`, collection `writing_descriptors`; script đồng bộ ID và loại ID cũ trong collection này, giữ nguyên các collection khác.

Muốn trích lại từ PDF đã kèm:

```powershell
.venv/Scripts/python.exe -B scripts/extract_descriptors.py
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py --validate-only
```

## Cách nối retrieval

Truy vấn Chroma phải hard-filter cả `test_part` và `criterion`, ví dụ:

```python
where = {"$and": [{"test_part": "task1"}, {"criterion": "task_achievement"}]}
```

Đưa đúng `chunk_id` đã retrieval vào `descriptor_refs` của lượt chấm. Không sửa ID hoặc đổi tên metadata để phục vụ schema riêng mà không có adapter. Chỉ collection descriptors dùng cho rubric; không trộn corpus plagiarism hoặc benchmark vào index này.

Band 0 là ô chung cả bốn tiêu chí trong PDF, được giữ tại `band_zero_policies` của provenance. Không tạo bốn descriptor độc lập giả cho Band 0; Member 2 phối hợp Member 3 khi dùng các policy này. Không tự coi mọi bài thiếu từ hoặc có cờ đạo văn là Band 0.

## Kiểm tra tiếp nhận

Chạy `python -m pytest tests/test_descriptor_data.py tests/test_rebuild_vectorstore.py`. Xác nhận 72 ID, đủ cả hai Task/bốn tiêu chí, query không lẫn Task/tiêu chí và rebuild không nhân đôi. Tests lưu trữ dùng embedding tất định để kiểm tra Chroma, không đo chất lượng truy hồi ngữ nghĩa; đánh giá retrieval dùng bộ truy vấn độc lập của Member 2.
