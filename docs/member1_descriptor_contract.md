# Contract dữ liệu descriptors cho Người 2 và Người 4

## Dữ liệu bàn giao

`data/processed/writing_descriptors.json` là object gồm `meta` và `chunks`.
`chunks` có 72 record: 2 Task × 4 tiêu chí × band nguyên 1–9, theo PDF May 2023.
Một record có đúng 7 trường: `text` và 6 metadata dưới đây.

| Trường | Quy ước |
|---|---|
| chunk_id | Duy nhất, ổn định, tối đa 100 ký tự thuộc `[A-Za-z0-9_.:-]` |
| test_part | `task1` hoặc `task2`; không có shared/task1_task2 |
| criterion | Task 1: task_achievement; Task 2: task_response; cả hai có coherence_cohesion, lexical_resource, grammatical_range_accuracy |
| band | Band nguyên 1–9 đúng hàng nguồn; không nội suy |
| version | ielts_writing_2023_05 |
| source_url | https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf |
| text | Nội dung ô đúng Task, chỉ gộp xuống dòng thành khoảng trắng và phục hồi hai glyph dấu câu lỗi |

Nguồn có cả Academic/General Training; giữ nhãn trong ô Task Achievement và chỉ áp dụng
phần Academic cho sản phẩm này. Không thay descriptors Task 1 bằng bản Task 2.

Band 0 là hàng dùng chung theo từng bảng, nằm trong
`data/processed/descriptor_provenance.json:band_zero_policies`, không nạp collection.
Người 2/3 cần xử lý policy này riêng khi phù hợp; không hiểu thiếu chunk Band 0 là không tồn tại Band 0.
File provenance còn có trang PDF (từ 1), bounding box từng ô, SHA256 và ghi chú cách áp dụng bảng.
Bold trong nguồn biểu thị giới hạn đánh giá; JSON plain text chưa biểu diễn định dạng bold.
Chưa có xác nhận kiểm tra chéo bởi thành viên thứ hai; không tuyên bố đã nghiệm thu nội dung.

## Cài đặt và tái tạo

Python 3.11–3.14, chạy tại repo root:

```powershell
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -B scripts/extract_descriptors.py --pdf ielts-writing-band-descriptors.pdf
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py --validate-only
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py
```

Tải PDF từ URL chính thức ở trên về đường dẫn đó trước khi extract.
Có thể tải nguồn bằng `scripts/download_descriptors.py` trước bước extract. Extractor chỉ hỗ trợ layout 9 trang May 2023; phiên bản khác phải rà lại parser.
Không tải PDF tự động hoặc tự ghi ngày tải giả; `download_info.json` là ghi nhận ban đầu.

## ChromaDB

- Path mặc định: `data/chroma_db/`, collection: `writing_descriptors`.
- Embedding: Chroma `DefaultEmbeddingFunction`, local ONNX `all-MiniLM-L6-v2`.
- Lần đầu cần mạng để tải model; không cần LLM API key. Không dùng embedding giả khi tải lỗi.
- Documents = text; metadata giữ đủ sáu trường; Chroma ID = chunk_id.
- Validate và embed trước khi ghi; upsert records rồi loại ID cũ chỉ trong collection này.
- Không xóa cả DB hoặc collection khác. Rebuild không phải transaction nguyên tử;
  dừng app đọc DB khi cập nhật, chạy lại nếu quá trình ghi bị ngắt.
- Không thay embedding model trên collection cũ. Khi đổi model, dùng DB path mới.
- Script mặc định dùng đường dẫn tính từ repo, không phụ thuộc working directory.

Người 2 mở lại bằng cùng embedding:

```python
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection("writing_descriptors", embedding_function=DefaultEmbeddingFunction())
result = collection.query(
    query_texts=["How effectively are paragraphs and ideas organized?"],
    n_results=3,
    where={"$and": [{"test_part": "task2"}, {"criterion": "coherence_cohesion"}]},
)
# Ghép result ids/documents/metadatas thành DescriptorChunk; không trả cấu trúc Chroma thẳng cho Agent.
```

Người 4 nhận các chunk thực sự truy xuất của lượt đó, không nhận toàn bộ 72 chunk để
kiểm tra refs. Corpus plagiarism chưa được làm trong bước 1–4 này.

## Kiểm chứng và giới hạn

Test cấu trúc không chứng minh AI chấm đúng, không thay thế benchmark 30 bài.
Integration test dùng Chroma thật với embedding deterministic chỉ để kiểm tra lưu trữ,
lọc metadata, stale ID và bảo toàn collection khác; model thật được kiểm tra qua rebuild CLI.
Test source cần PDF local; không tự skip nếu thiếu nguồn.
Các dependency cài thực tế được ghi trong requirements.txt (Windows, Python 3.14).
requirements.txt ghim hai dependency trực tiếp; không phải lock toàn bộ dependency bắc cầu.

Kết quả kiểm chứng ngày 19/10/2026: 8 unittest đạt; rebuild với embedding thật chạy
hai lần đều giữ 72 records. Integration test kiểm tra đủ document/metadata, bộ lọc,
loại stale ID và không thay đổi collection khác. Chưa đánh giá precision/recall retrieval.
