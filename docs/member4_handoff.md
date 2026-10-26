# Bàn giao TV4 — tích hợp corpus và công cụ kiểm chứng

Cập nhật 26/10/2026 trên nhánh `feat/linh/deterministic-tools`.

## 1. Những gì đã nối

- Đọc trực tiếp corpus TV1 `data/corpus_plagiarism/corpus.jsonl`: 1.800 bài, 600 Task 1 và 1.200 Task 2.
- Chấp nhận sáu trường TV1, giữ nguyên `text`, `source_id`, URL và metadata; không tự thêm giấy phép.
- Giữ tương thích mảng JSON/JSONL cũ với `license` nếu nguồn đã có trường đó.
- Chỉ mục corpus mặc định được dùng lại giữa các request. File thay đổi mtime/kích thước sẽ nạp lại; thiếu/hỏng vẫn báo lỗi.
- Validators nhận tên tiêu chí canonical lẫn tên cũ có `_and_`; không sửa `chunk_id` hoặc nội dung descriptors.
- Adapter TV3 gọi đúng hàm `compute_band` của TV4, không có phép tính raw mean riêng.
- Chế độ live dùng retriever TV2, công cụ TV4, validators/security thật; không dùng `FakeTools`/`FakeRetriever`.
- API giữ tên tiêu chí cũ cho frontend hiện tại; graph vẫn dùng enum canonical.
- Frontend giữ nguyên bài nộp, đổi tọa độ Unicode Python sang UTF-16 JavaScript và xử lý dẫn chứng chồng nhau.
- Runner TV5 đọc được `case_id`/`id`, `exam_question`, `scores.overall_band` và điều kiện `expected` của TV1.

## 2. Các hàm TV3/TV5 sử dụng

```python
from agent.tools.compute_tool import count_words, compute_band
from agent.tools.plagiarism_tool import check_plagiarism, get_default_checker
from agent.tools.security_tool import SecurityGuard
from skills.writing_assessment.validators import (
    quote_validator, refs_validator, consistency_validator,
)
```

`check_plagiarism(essay)` dùng corpus TV1 và index được cache. `get_default_checker().entries`
cho phép tra `source_id` về `source_url`. Nếu host cung cấp corpus khác, khởi tạo
`PlagiarismChecker.from_file(path)` một lần rồi truyền checker cho `build_team_dependencies`.

`CorpusEntry` cần `source_id`, `text`, `source_url`; `license`, `task_type`,
`exam_question`, `topic` là metadata tùy chọn. Metadata có cung cấp phải hợp lệ.
Các bài có ID trùng, thiếu nội dung/nguồn, ID sai định dạng hoặc JSON hỏng đều bị từ chối.
File corpus không bị loader sửa hay tải lại từ Internet.

Kết quả tool:

```text
PlagiarismResult(possible_plagiarism, max_similarity, matches)
matches: [{source_id, evidence: {quote, start_char, end_char}}]
SecurityResult(injection_detected)
ValidationIssue(code, criterion, reason, path)
```

Offset là chỉ số Unicode code point, cuối không bao gồm ký tự:
`essay[start_char:end_char] == quote`. Không trim/normalize bài sau khi tính offset.

## 3. Quy ước tính điểm

`compute_band([6,6,6,7]) == 6.5`; `[6,7,7,7] == 7.0`.
Lấy trung bình bốn điểm rồi làm tròn nấc 0.5, hòa thì lên theo quy ước repository
trong AGENTS.md/phân công. Đây không phải tuyên bố quy tắc chấm Task chính thức của IELTS.
Công cụ nhận bốn số hữu hạn 0–9, từ chối bool/NaN/inf. Mock graph và adapter dùng cùng hàm.
DTO canonical cho phép điểm tiêu chí hữu hạn 0–9; wrapper cũ nhận cùng phạm vi,
chuẩn hóa tên tiêu chí khi nhận model canonical và kiểm tra tổng bằng cùng hàm TV4.

## 4. Corpus và thuật toán

Thuật toán giữ cụm 5 từ liên tiếp. Với từng nguồn, tính số token bài nộp được cụm trùng
bao phủ chia cho tổng token bài nộp. `max_similarity` là giá trị lớn nhất với MỘT nguồn.
Mặc định cờ nghi ngờ cần độ phủ >=0.8 và >=20 từ trùng với nguồn đó.
Đề bài/chủ đề không được ghép vào `text` để tính trùng.

Ngưỡng còn cần hiệu chỉnh bằng tập đạo văn có nhãn riêng. Không diễn giải similarity
là xác suất đạo văn, không tuyên bố phát hiện >=90% / gắn nhầm <=10% chỉ dựa trên unit test.
Bài diễn đạt lại và chép ghép nhiều nguồn vẫn là giới hạn của thuật toán.

## 5. Nối graph với công cụ thật

Dùng `src.agent.team_adapters.build_team_dependencies(task_bank=bank, examiner=examiner)`.
Mặc định tools đọc corpus TV1. Có thể truyền `plagiarism_checker=checker` và
`retriever=retriever` đã khởi tạo để host quản lý vòng đời.
`TeamRetriever` xác thực DTO TV3; `TeamValidators` ánh xạ tên criterion cũ/mới.
Lỗi dữ liệu/công cụ làm graph trả `DEPENDENCY_UNAVAILABLE` hoặc `RETRIEVAL_INVALID`,
không biến thành kết quả không đạo văn. Lỗi chấm sai refs/schema/evidence chỉ được sửa tối đa 2 lần.

## 6. API và Task 1

`POST /api/assess-writing` giữ `task_type`, `prompt`, `essay`, `mock` và thêm:

- `task_material_text`: số liệu/đơn vị/chú giải đầy đủ cho Task 1 ở chế độ live.
- `source_url`: URL HTTPS tùy chọn cho đề public. Không tự nhận đề public là self-written/CC0.

Graph text-only không tự hiểu ảnh chỉ từ đường dẫn `material` trong JSON TV1.
TV5 cần cung cấp bản chép biểu đồ chính xác qua `task_material_text`, hoặc bổ sung adapter
thị giác trước khi đánh giá Task 1 bằng ảnh. Thiếu dữ liệu này trả 422 thay vì chấm đoán.
Frontend đã có ô nhập số liệu Task 1. Đề Task 2 live cũng không được để trống.

Lỗi live có `detail.code`, `retry_count`, `errors`, `diagnostics` đã lọc:
422 đầu vào; 503 thiếu cấu hình/corpus/retrieval; 429 rate limit; 504 timeout;
502 lỗi provider hoặc hết lượt sửa. Không trả điểm khi thất bại.
Mock backend vẫn gọi corpus/security thật; lỗi corpus không bị bỏ qua.

## 7. Điều kiện chạy thật

Cài dependency đã khai báo trong requirements.txt. Từ Git Bash ở gốc repo:

```bash
.venv/Scripts/python.exe -B scripts/check_member1_data.py
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py --validate-only
.venv/Scripts/python.exe -B scripts/rebuild_vectorstore.py
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

ChromaDB phải được tạo trước khi chấm live; script rebuild có thể cần mạng để tải model embedding.
Xem `.env.example`: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_RESPONSE_FORMAT`.
Không cần API key cho kiểm tra corpus hoặc các test offline. Không bật tracing dữ liệu thật mặc định.

## 8. Kiểm thử và runner TV5

```bash
.venv/Scripts/python.exe -B -m pytest
node --test tests/test_frontend_evidence.cjs
.venv/Scripts/python.exe -B evals/run.py --mock --benchmark evals/benchmark_dev/benchmark.json
.venv/Scripts/python.exe -B evals/run.py --mock --benchmark evals/benchmark_test/benchmark.json
```

Runner mặc định đọc 69 bài dev, giữ 15 test riêng. Tham số đường dẫn vẫn nhận bộ demo cũ.
Khi live thiếu dữ liệu/cấu hình, runner ghi lỗi từng bài, không tạo điểm giả hoặc dừng cả batch.
Basic cases `scores=null` không tính MAE. Điều kiện flags/trần điểm/correction nằm trong
`functional_passed` và `functional_errors`. Mock kiểm tra luồng, không chứng minh độ chính xác mô hình.

`tests/test_team_corpus_integration.py` chạy corpus thật, N2 validation thật và graph/validators thật;
backend lưu trữ retrieval và examiner được kiểm soát, không phải inference Chroma/LLM thật.
`tests/test_frontend_evidence.cjs` kiểm tra Unicode, đoạn chồng nhau và tọa độ sai trên renderer thật.

## 9. Kiểm chứng ở máy này (26/10/2026)

- 317 test Python pass; 1 test Chroma được skip, 1 test trích PDF được deselect,
  và module tests/test_rebuild_vectorstore.py chưa chạy vì môi trường thiếu chromadb/PyMuPDF.
- 3 test renderer Node pass. Ruff, schema sync canonical, kiểm tra repository và lịch sử Git pass.
- Runner MOCK xử lý đủ 69 dev và 15 test; tất cả bài benchmark qua kiểm tra cấu trúc/evidence.
- Basic cases: 5/6 điều kiện hành vi đạt trong MOCK. Case lạc đề nâng cao chưa đạt;
  bộ giả lập dùng heuristic từ khóa, không thay khả năng hiểu đề của LLM.
- Chưa chạy inference Chroma/LLM thật; chưa báo cáo độ chính xác chấm band hoặc tỷ lệ phát hiện đạo văn thực tế.
