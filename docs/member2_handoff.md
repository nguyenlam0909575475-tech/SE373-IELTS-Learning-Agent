# Bàn giao thành viên 2 cho thành viên 3 4 và 5

Phạm vi Phase 1: retrieval cho UC-02 và skill `writing-assessment`. Code nằm trên
nhánh `feat/member2-retrieval-skill`, xuất phát từ nhánh dữ liệu của thành viên 1.
Không cần API key để chạy retrieval hoặc unit tests.

## File bàn giao

| File | Công dụng |
|---|---|
| `src/tools/rag_descriptors.py` | Retriever đồng bộ, DTO adapter, lỗi có cấu trúc, policy Band 0 riêng |
| `tests/test_retrieval.py` | Kiểm Task/criterion, metadata, lỗi và Chroma thật với embedding giả lập |
| `skills/writing-assessment/skill.yaml` | Contract I/O theo handoff TV3, khai báo schema authority |
| `skills/writing-assessment/instructions.md` | Các bước chấm, ranh giới dữ liệu, giới hạn sửa và final checks |
| `skills/writing-assessment/SKILL.md` | Điểm vào để khám phá skill |
| `skills/writing-assessment/checks.py` | Điểm vào gọi `src.skill_checks.run_checks` |
| `src/skill_checks.py` | Chuyển tiếp các validators được inject từ TV4 |
| `scripts/sync_writing_schema.py` | Xuất/kiểm tra JSON Schema từ model TV3 thật sau khi merge |
| `evals/retrieval_eval.py`, `evals/data/retrieval_queries.json` | Đo Precision/Recall/MRR trên tập truy vấn riêng |
| `scripts/demo_retrieval.py` | Demo tám scope và xuất trace chỉ chứa metadata |
| `docs/member2_rag_skill_report.md` | Nội dung báo cáo RAG/skill và kịch bản demo |

## Cài và tái tạo dữ liệu

Từ root repo trong PowerShell:

```powershell
py -3.14 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -B scripts/download_descriptors.py
.venv/Scripts/python.exe -B scripts/extract_descriptors.py
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py
```

Nếu downloader gặp HTTP 403, mở URL nguồn trong tài liệu TV1 và lưu PDF vào root.
Trong lần kiểm chứng này, curl tải được cùng URL và hash khớp:

```powershell
curl.exe -L --fail --output ielts-writing-band-descriptors.pdf https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf
Get-FileHash -LiteralPath ielts-writing-band-descriptors.pdf -Algorithm SHA256
```

Chỉ tiếp tục khi SHA256 là
`e3c88943ef92d98988ce4db454fd7fa8d8435f0b25e9ec667e3720a5c1168d1b`.
Không bỏ kiểm hash nếu nguồn thay đổi. PDF, JSON descriptors, provenance, ChromaDB
và `.venv` là dữ liệu local được ignore, không phải file cần thêm vào commit.
Downloader dùng urllib và curl có thể có kết quả HTTP khác nhau; không cần sửa
script TV1 để hoàn thành phần retrieval.

## Gọi tool

```python
from src.tools.rag_descriptors import DescriptorRetriever, RetrievalError

retriever = DescriptorRetriever()
try:
    chunks = retriever.retrieve_descriptors("task2", "lexical_resource", top_k=3)
except RetrievalError as error:
    # Chuyển thành dependency failure của graph, không chấm khi thiếu rubric.
    code, reason = error.code, error.reason
else:
    ref_ids = [chunk.chunk_id for chunk in chunks]
```

Hàm module `retrieve_descriptors(task_type, criterion, top_k=3)` cũng có cùng
contract. Dùng object để tái sử dụng kết nối và cấu hình `db_path` khác.
`task_type` và `criterion` nhận string hoặc enum có `.value`; `top_k` là số
nguyên 1–3, không nhận bool. Không chấp nhận Task/criterion không khớp.

Collection: `writing_descriptors`, path mặc định tính từ repo root, không từ
working directory của caller. Dùng cùng `DefaultEmbeddingFunction` với TV1,
model ONNX `all-MiniLM-L6-v2`. Không tạo collection/DB rỗng khi thiếu dữ liệu.
Chroma có thể tạo file phụ khi mở persistent DB; quyền tool ở đây là chỉ đọc
nội dung collection: không add/upsert/delete, không ghi hồ sơ người học.

Kết quả là list 1–3 record có bảy trường:
`chunk_id`, `test_part`, `criterion`, `band`, `version`, `source_url`, `text`.
Band ở nguồn này là int 1–9; không tự tạo chunk nửa band hay Band 0.
Kết quả giữ thứ tự xếp hạng của Chroma và ID nguồn, không kèm distance/score vào DTO.

## Nối với thành viên 3

Code TV3 thật chưa có trong checkout và chưa thấy nhánh tương ứng khi kiểm tra
GitHub ngày 20/10/2026. Không tạo lại `WritingAssessment`/`DependencyFailure`.

Sau merge, truyền class `DescriptorChunk` thật của TV3 vào
`DescriptorRetriever(chunk_factory=DescriptorChunk)`; factory nhận đúng bảy
keyword fields trên. Gán retriever này vào dependency `retriever` của graph.
Để ánh xạ lỗi, dùng:

```python
from src.tools.rag_descriptors import DescriptorRetriever, Member3RetrieverAdapter

# Member3DescriptorChunk và make_member3_failure do lớp composition root cung cấp.
retriever = Member3RetrieverAdapter(
    DescriptorRetriever(chunk_factory=Member3DescriptorChunk),
    failure_factory=make_member3_failure,
)
```

`make_member3_failure(code)` phải trả **instance DependencyFailure thật** của TV3,
có mã `RETRIEVAL_INVALID`. Chưa biết constructor/import thực tế nên không tự đoán.
Nếu graph đã tự ánh xạ RetrievalError thì không cần adapter này.

Người 3 phải nạp nội dung `instructions.md` vào examiner và ghi skill invocation
`writing-assessment`, version `1.0.0` trong trace. File skill nằm trong repo chưa
đồng nghĩa graph đã thực thi skill. Dữ liệu không tin cậy không được đặt trong
system instructions. Đưa **tất cả và chỉ các chunks thực tế của lượt chấm** cho
refs validator; không dùng cả collection làm whitelist.

Schema snapshot trong YAML theo handoff; khi model TV3 có mặt:

```powershell
.venv/Scripts/python.exe -B -m scripts.sync_writing_schema --module agent.schemas
.venv/Scripts/python.exe -B -m scripts.sync_writing_schema --module agent.schemas --check
```

Nếu package sau merge là `src.agent.schemas`, đổi `--module` tương ứng. Script
xuất trực tiếp `WritingAssessment.model_json_schema()` vào `output.json_schema`
trong `skill.yaml` và
`skills/writing-assessment/writing_assessment.schema.json`; chưa có model thì
báo lỗi và không sinh schema giả. Bổ sung `--check` vào CI sau merge để bắt schema drift.

Policy Band 0: `retriever.get_band_zero_policy("task1")` đọc provenance TV1,
kiểm source URL/hash và trang, trả `test_part`, `band=0`, `text`, `source_page`.
Không có `chunk_id`; không đưa vào descriptor_refs. Đây là kênh riêng để TV3
tích hợp; chưa xác nhận xử lý Band 0 end-to-end. TV3 cần thống nhất schema/luồng
cho trường hợp Band 0, tránh ép validator yêu cầu refs giả.

## Nối với thành viên 4

```python
from src.skill_checks import run_checks

# assessment đã qua Pydantic của TV3; validators là Member4Validators thật.
issues = run_checks(
    assessment, essay, chunks,
    validators=validators,
    word_count=word_count,
    overall_band=overall_band,
    plagiarism=plagiarism,
    security=security,
    off_topic=off_topic,
)
```

Các biến bên phải là kết quả tools/security và quyết định off-topic của graph,
không đọc lại từ assessment đang kiểm tra. Hàm chuyển tiếp quote_validator,
refs_validator, consistency_validator, giữ nguyên object ValidationIssue.
Trả `[]` khi đạt; lỗi vận hành truyền lên caller, không giả thành `[]`.
Không import cứng module TV4, không viết lại validator. Các test dùng object giả
để kiểm thứ tự/keyword/return shape, chưa phải kiểm tích hợp với code TV4 thật.

Theo TV3 và TV4 mới: `compute_band([6,6,6,7]) = 6.25`, không làm tròn ở cấp Task.
`overall_band` vẫn là tên trường đúng. TV3 quản lý tối đa hai lượt repair;
checks không tự gọi LLM và không thêm validation errors vào `flags`.

## Kiểm thử và đo chất lượng

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
.venv/Scripts/python.exe -B -m evals.retrieval_eval
.venv/Scripts/python.exe -B -m scripts.demo_retrieval
```

Lần kiểm chứng 20/10/2026: toàn bộ **38 tests đạt**, gồm 8 tests TV1 và 30 tests
TV2; Chroma integration test dùng DB thật với embedding deterministic. Không dùng
chúng để khẳng định chất lượng embedding. Eval ranking chạy embedding thật,
kết quả lưu ở `docs/member2_retrieval_results.json`; giải thích ở báo cáo RAG/skill.
Lệnh eval mặc định ghi vào `artifacts/member2/` (ignore). Trace demo mặc định
cũng nằm ở đó; bản bàn giao có thể lưu ở `traces/samples/member2_retrieval.json`.
Fixture embedding của test rebuild TV1 được đổi từ vector giống hệt nhau sang
vector ổn định theo hash text để tránh kết quả ANN không ổn định; giữ nguyên
các assertion nghiệp vụ và không thay code rebuild TV1.

Sau merge cần: DTO TV3 thật; adapter failure thật; validators TV4 thật; graph nạp
skill và ghi trace; thử lỗi refs/quote rồi repair, hết hai lượt thì dừng. Người 5
chạy eval chấm Writing trên benchmark hợp lệ. Không tính 16 truy vấn retrieval
là 16 bài chấm chuẩn hoặc là nghiệm thu UC-02.
