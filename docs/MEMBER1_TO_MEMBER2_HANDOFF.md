# Bàn giao kho IELTS Writing descriptors từ Người 1 cho Người 2

## Phạm vi

Nhánh `member1-Ielts-band-descriptors&script` cung cấp contract dữ liệu, script lấy nguồn,
trích xuất từng ô, validation và dựng ChromaDB. Người 2 triển khai retrieval và skill.
Không gồm Agent, frontend, thuật toán plagiarism, corpus hay benchmark.

## File và thư mục

| File | Công dụng |
|---|---|
| requirements.txt | Hai thư viện trực tiếp, ghim phiên bản đã cài |
| scripts/download_descriptors.py | Tải PDF chính thức, kiểm SHA256 và ghi ngày tải thật |
| scripts/extract_descriptors.py | Tách bảng thành 72 chunks riêng từng Task |
| scripts/descriptor_data.py | Contract và kiểm tra dữ liệu trước khi nạp |
| scripts/rebuild_vectorstore.py | Tạo embedding, upsert Chroma và loại ID cũ |
| tests/ | Test cấu trúc, nguồn và lưu trữ/filter DB |
| docs/member1_descriptor_contract.md | Chi tiết schema, model và giới hạn |
| docs/data_sources.md | Nguồn, bản quyền, trạng thái dữ liệu |
| data/raw/descriptors/ | Metadata nguồn, không chứa PDF công khai |
| data/processed/ | Hướng dẫn; JSON được tạo local |
| data/chroma_db/ | Hướng dẫn; binary được tạo local |

## Cách chạy từ checkout mới

Windows PowerShell, đứng tại root của repo:

```powershell
git switch 'member1-Ielts-band-descriptors&script'
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -B scripts/download_descriptors.py
.venv/Scripts/python.exe -B scripts/extract_descriptors.py
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py --validate-only
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py
```

Nếu downloader báo HTTP 403, mở URL chính thức trong trình duyệt và lưu PDF vào root với tên `ielts-writing-band-descriptors.pdf`, rồi tiếp tục extract. Máy kiểm chứng gặp HTTP 403 khi tải tự động; extract/test/rebuild được chạy với PDF local sẵn có.

Chroma tải model local `all-MiniLM-L6-v2` lần đầu; cần mạng, không cần LLM API key.
PDF và JSON toàn văn chưa xác minh quyền phân phối lại nên không được commit.
SHA256 khác nguồn đã kiểm tra thì downloader dừng; không bỏ kiểm tra chỉ để chạy tiếp.

## Đầu ra Người 2 nhận

- `data/processed/writing_descriptors.json`: object `{meta, chunks}`, 72 records.
- `data/processed/descriptor_provenance.json`: trang/bounding box, hash PDF và Band 0 riêng.
- `data/chroma_db/`: collection `writing_descriptors`, model `all-MiniLM-L6-v2`.
- Mỗi record gồm text + chunk_id, test_part, criterion, band, version, source_url.
- `test_part` chỉ task1/task2. Không dùng shared/task1_task2 hoặc all_criteria.
- Task1 dùng task_achievement, Task2 dùng task_response; ba tiêu chí còn lại là
  coherence_cohesion, lexical_resource, grammatical_range_accuracy.
- Band nguyên 1–9 theo bảng; Band 0 là policy riêng, không nội suy descriptor nửa band.

## Cách truy vấn

```python
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

client = chromadb.PersistentClient(path='data/chroma_db')
collection = client.get_collection('writing_descriptors', embedding_function=DefaultEmbeddingFunction())
result = collection.query(
    query_texts=['organization of ideas and paragraphs'],
    n_results=3,
    where={'$and': [{'test_part': 'task2'}, {'criterion': 'coherence_cohesion'}]},
)
chunks = [dict(metadata, text=text) for metadata, text in
          zip(result['metadatas'][0], result['documents'][0])]
```

Người 2 viết `retrieve_descriptors(task_type, criterion, top_k=3)` trả chunks đúng shape.
Giữ chunk_id; kiểm metadata; trả lỗi khi rỗng/sai thay vì tự tạo tiêu chí.
Chuyển đúng tập chunks của lượt chấm cho Agent/validator, không truyền cả kho làm refs hợp lệ.
Không dùng model embedding khác để query collection này.

## Kiểm tra nghiệm thu

1. Từ checkout mới tải nguồn và tạo đủ 72 chunks.
2. Chạy toàn bộ tests; rebuild lặp không nhân đôi records.
3. Query từng Task/criterion chỉ trả metadata đúng bộ lọc.
4. Hai người kiểm tra chéo JSON với PDF, nhất là ô nhiều dòng và chữ đậm.
5. Đo precision/recall retrieval trên tập truy vấn của Người 2; test DB chưa đo chất lượng RAG.

Rebuild không nguyên tử: dừng reader khi cập nhật và chạy lại nếu bị ngắt.
Test nguồn cần PDF local; không bỏ qua test nếu chưa tải PDF.
Không push .venv, PDF, JSON toàn văn, DB binary hoặc bài người học thật.
Không có năm tài liệu phân công/rubric/handoff cũ trong snapshot nhánh này.

## Minh bạch AI

AI hỗ trợ viết parser, validation, rebuild, tests và hướng dẫn bàn giao.
Thành viên cần đọc hiểu code; kiểm tra tự động không thay thế kiểm tra nội dung độc lập.
