# Bàn giao IELTS Writing descriptors từ Người 1 cho Người 2

## Phạm vi và file bàn giao

Nhánh `member1-IELTS-Band-Descriptors-Data&Script` cung cấp contract, script lấy nguồn,
trích xuất, validation và tạo ChromaDB. Người 2 tiếp tục triển khai retrieval và skill.
Chưa gồm corpus, benchmark, Agent hoặc UI. Đây là tài liệu gộp thay hai tài liệu handoff/contract cũ.

| File hoặc thư mục | Công dụng |
|---|---|
| requirements.txt | Ghim hai dependency trực tiếp, chưa khóa mọi dependency bắc cầu |
| scripts/download_descriptors.py | Tải PDF chính thức, kiểm hash, ghi metadata tải khi thành công |
| scripts/extract_descriptors.py | Trích từng ô theo Task, tách policy Band 0 |
| scripts/descriptor_data.py | Contract và validation trước khi ghi DB |
| scripts/rebuild_vectorstore.py | Embed, upsert và loại ID cũ trong collection |
| tests/ | Test dữ liệu, nguồn, lưu trữ và metadata filters |
| docs/data_sources.md | Nguồn và trạng thái quyền sử dụng |
| data/raw/descriptors/download_info.json | Metadata nguồn |
| data/processed/ | JSON sinh local |
| data/chroma_db/ | DB sinh local |

## Cài bằng Python và pip không cần uv

Windows PowerShell, đứng ở root repo. Cần Python có venv và pip. Đã kiểm chứng code
trên Windows/Python 3.14, chưa xác nhận mọi phiên bản Python khác.
Gọi Python trong .venv nên không cần activate hoặc đổi ExecutionPolicy.

```powershell
git switch 'member1-IELTS-Band-Descriptors-Data&Script'
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Nếu máy chỉ nhận py, thay python bằng py ở lệnh tạo venv. Nếu đã kích hoạt môi trường
Python riêng, dùng `python -m pip install -r requirements.txt`.
Nhánh bàn giao dùng requirements.txt, không cần requirements-data.txt của workspace cũ.
Dùng python -m pip để cài đúng môi trường Python đang gọi.

Nếu đã có uv, có thể dùng phương án tương đương thay cho bước cài trên:

```powershell
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
```

## Lấy nguồn và chạy pipeline

Nguồn: [IELTS Writing Band Descriptors May 2023](https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf).

```powershell
.venv/Scripts/python.exe -B scripts/download_descriptors.py
```

Máy kiểm chứng gặp HTTP 403 khi tải tự động. Nếu gặp lỗi này, mở URL bằng trình duyệt,
lưu ở root với tên ielts-writing-band-descriptors.pdf rồi tiếp tục:

```powershell
.venv/Scripts/python.exe -B scripts/extract_descriptors.py
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py --validate-only
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py
```

Extractor chỉ hỗ trợ layout 9 trang May 2023. Nguồn khác/hash khác cần kiểm tra parser,
không bỏ kiểm tra hash chỉ để chạy tiếp. Downloader ghi ngày tải thật khi tải thành công;
extractor không tự xác nhận ngày tải thủ công. PDF và JSON toàn văn chưa xác minh quyền
phân phối lại nên được giữ local/ignore. Chroma tải model lần đầu, cần mạng, không cần API key.

## Contract dữ liệu

writing_descriptors.json là object gồm meta và chunks. Mỗi chunk có đúng bảy trường:
text và sáu metadata. Không thay descriptors Task 1 bằng nội dung Task 2.

| Trường | Quy ước |
|---|---|
| chunk_id | Duy nhất, ổn định, tối đa 100 ký tự thuộc [A-Za-z0-9_.:-] |
| test_part | task1 hoặc task2; không dùng shared/task1_task2 |
| criterion | Task1 dùng task_achievement, Task2 dùng task_response; cả hai có coherence_cohesion, lexical_resource, grammatical_range_accuracy |
| band | Nguyên 1–9 theo ô nguồn, không nội suy band nửa |
| version | ielts_writing_2023_05 |
| source_url | URL PDF chính thức ở trên |
| text | Nội dung đúng ô; gộp xuống dòng thành khoảng trắng, phục hồi hai glyph dấu câu lỗi |

Giữ nhãn Academic/General Training trong ô nguồn, chỉ áp dụng phần Academic cho dự án.
Plain text chưa biểu diễn bold; chữ đậm trong PDF chỉ các đặc điểm giới hạn mức đánh giá.

## Band 0 và bằng chứng từ PDF

Đã xem trực tiếp hai trang PDF local ngày 20/10/2026:

| Bảng | Trang PDF tính từ 1 | Trang in trên bảng | Bố cục hàng Band 0 |
|---|---|---|---|
| Task 1 | 5 | Page 3 | Một ô nội dung kéo ngang cả bốn cột tiêu chí |
| Task 2 | 9 | Page 3 | Một ô nội dung kéo ngang cả bốn cột tiêu chí |

Các hàng Band 1–9 có ô riêng theo tiêu chí; Band 0 không có bốn mô tả độc lập.
Hàng gộp nêu chung các tình huống không làm bài, toàn bài dùng ngôn ngữ khác tiếng Anh,
hoặc có bằng chứng câu trả lời được học thuộc toàn bộ. Đó là căn cứ biểu diễn thành
policy chung từng Task, không phải chỉ vì muốn có đủ 72 chunks.
Không suy diễn rằng mọi bài ngắn, bài yếu hoặc có cờ possible_plagiarism đều là Band 0.

Extractor giữ hai record tại
`data/processed/descriptor_provenance.json` → `band_zero_policies`,
gồm test_part, band=0, text, source_page. Nội dung không bị xóa khỏi dữ liệu; chỉ không
đưa vào collection criterion × band để tránh enum all_criteria hoặc nhân bản hàng gộp.
Provenance còn có trang/bounding box từng ô Band 1–9 và SHA256 nhận diện PDF đã đọc.

72 = 2 Task × 4 tiêu chí × 9 band chỉ chứng minh độ phủ lưới Band 1–9, chưa đủ chứng minh
đúng nội dung hoặc xử lý đủ mọi band. Nghiệm thu phải mở trang PDF 5/9 đối chiếu nguyên văn
hai policy và kiểm tra 72 ô còn lại không mất câu, sai Task, sai hàng hoặc lẫn cột.

Người 2 cần đọc policy theo Task và bàn giao qua kênh policy/instructions riêng cho Người 3,
không trộn vào list DescriptorChunk theo tiêu chí. Hiện pipeline chưa tự nạp Band 0 vào Agent;
interface và hành vi cần Người 2/3 thống nhất rồi kiểm thử. Không tạo chunk ID Band 0 giả
cho descriptor_refs vì validator chỉ nhận chunk thực sự truy xuất của lượt đó.
Chưa nghiệm thu Band 0 end-to-end hoặc có xác nhận kiểm tra chéo từ thành viên thứ hai.

## ChromaDB và retrieval

- Path: data/chroma_db; collection: writing_descriptors.
- Embedding: DefaultEmbeddingFunction, local ONNX all-MiniLM-L6-v2.
- Document = text; metadata = sáu trường; Chroma ID = chunk_id.
- Validate và embed trước khi ghi; upsert rồi loại ID cũ chỉ trong collection này.
- Không đụng collection khác. Rebuild không nguyên tử: dừng reader khi cập nhật,
  chạy lại nếu ghi bị ngắt. Khi đổi model embedding, dùng DB path mới.
- Script tính path mặc định từ repo root; ví dụ query dưới đây chạy ở root.

```python
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

client = chromadb.PersistentClient(path='data/chroma_db')
collection = client.get_collection(
    'writing_descriptors', embedding_function=DefaultEmbeddingFunction()
)
result = collection.query(
    query_texts=['organization of ideas and paragraphs'],
    n_results=3,
    where={'$and': [
        {'test_part': 'task2'},
        {'criterion': 'coherence_cohesion'}
    ]},
)
chunks = [dict(metadata, text=text) for metadata, text in
          zip(result['metadatas'][0], result['documents'][0])]
```

Người 2 viết retrieve_descriptors(task_type, criterion, top_k=3), kiểm Task/criterion,
giữ ID và trả đúng shape. Rỗng/sai metadata thì trả lỗi, không tự tạo rubric.
Chuyển đúng chunks của lượt chấm cho Agent/validator, không coi cả kho là refs hợp lệ.
Người 2 tiếp tục làm skill và đo chất lượng retrieval; chưa có precision/recall từ phần này.

## Checklist nghiệm thu cho Người 2

1. Cài bằng pip hoặc uv; lấy PDF, tái tạo JSON từ checkout mới.
2. Đủ 72 ô đúng Task/cột/band, ID duy nhất; kiểm nội dung với PDF.
3. Hai policy Band 0 khớp hàng gộp trang PDF 5/9; tách kiểm nguồn khỏi kiểm tích hợp Agent.
4. Tests chạy đạt; rebuild lặp không nhân đôi, không sửa collection khác.
5. Query đủ bốn tiêu chí của hai Task, metadata không lẫn Task.
6. Chốt cách nạp Band 0 với Người 3 và kiểm thử trước nghiệm thu end-to-end.
7. Đo precision/recall retrieval trên tập truy vấn độc lập.

Lần kiểm chứng code trước: 8 unittest đạt; rebuild với model thật hai lần giữ 72 records,
truy vấn thật lọc đúng Task/criterion. Integration test dùng embedding deterministic để
thử lưu trữ/filter, không đánh giá chất lượng embedding. Test nguồn cần PDF local,
không skip khi thiếu PDF. Các kết quả này không thay benchmark Writing.

## Nguồn và minh bạch AI

Xem data_sources.md. Không push .venv, PDF, JSON toàn văn, DB binary hoặc dữ liệu người học thật.
Năm tài liệu đề tài/rubric/phân công/handoff cũ đã được loại khỏi nhánh.
AI hỗ trợ parser, validation, rebuild, tests và tài liệu; thành viên cần đọc hiểu code.
