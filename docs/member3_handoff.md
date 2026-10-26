# Người 3 — Tên hàm và dữ liệu dùng chung

Contract chốt ngày 18/10/2026; trạng thái tích hợp nhóm cập nhật 24/10/2026. Quy ước đối chiếu nguồn IELTS chính thức.
Nguồn kiểu dữ liệu: [schemas.py](../src/agent/schemas.py) và [contracts.py](../src/agent/contracts.py).

## 1. Cách gọi và input

```python
from src.agent.graph import build_graph

graph = build_graph(dependencies=deps)
output = graph.invoke({"request": submission})
payload = output["result"].model_dump(mode="json")
```

`deps` là `Dependencies(task_bank, retriever, tools, examiner, validators, security,
model_version, prompt_version)`; hai version có giá trị mặc định. Input `submission`:

```json
{"item_id":"MOCK_T2_001","task_type":"task2","essay":"Free community libraries help residents learn because they offer shared books, quiet study spaces and practical information. Public funding should support these services while local councils review their costs and benefits."}
```

Chỉ nhận 3 trường trên. Đề lấy từ `TaskBank.resolve(item_id)`, không thêm `task_prompt` vào submission.

## 2. JSON kết quả

Mẫu MOCK dưới đây minh họa cấu trúc, dùng bài 31 từ ở mục 1 nên có `under_length`.
Điểm 6.0 là fixture, không phải nhận xét IELTS về bài này.

```json
{
  "status": "success",
  "run_id": "00000000-0000-4000-8000-000000000001",
  "assessment": {
    "task_type": "task2",
    "word_count": 31,
    "criteria": [
      {"criterion": "task_response", "band": 6.0, "evidence": [{"quote": "Free community libraries", "start_char": 0, "end_char": 24}], "descriptor_refs": ["MOCK_task2_task_response_6"], "comment": "MOCK fixed fixture; not an IELTS evaluation."},
      {"criterion": "coherence_cohesion", "band": 6.0, "evidence": [{"quote": "Free community libraries", "start_char": 0, "end_char": 24}], "descriptor_refs": ["MOCK_task2_coherence_cohesion_6"], "comment": "MOCK fixed fixture; not an IELTS evaluation."},
      {"criterion": "lexical_resource", "band": 6.0, "evidence": [{"quote": "Free community libraries", "start_char": 0, "end_char": 24}], "descriptor_refs": ["MOCK_task2_lexical_resource_6"], "comment": "MOCK fixed fixture; not an IELTS evaluation."},
      {"criterion": "grammatical_range_accuracy", "band": 6.0, "evidence": [{"quote": "Free community libraries", "start_char": 0, "end_char": 24}], "descriptor_refs": ["MOCK_task2_grammatical_range_accuracy_6"], "comment": "MOCK fixed fixture; not an IELTS evaluation."}
    ],
    "overall_band": 6.0,
    "corrections": [],
    "flags": ["under_length"],
    "disclaimer": "Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức"
  }
}
```

Quy ước cần khớp:

| Thành phần | Tên/giá trị |
|---|---|
| `criteria` | Đúng 4 mục; Task1 dùng `task_achievement`, Task2 dùng `task_response`; ba tiêu chí còn lại như mẫu |
| Mỗi `evidence` | `quote`, `start_char`, `end_char`; `essay[start_char:end_char] == quote` |
| Mỗi `corrections` | `original`, `suggestion`, `reason`, `category` (`grammar`/`lexis`/`cohesion`/`task`) |
| `flags` cho phép | `under_length`, `off_topic`, `possible_plagiarism`, `injection_detected` |
| Trường điểm / nhận xét | `overall_band` / `comment`; không dùng tên cũ `task_band` |

Offset từ 0, theo Python Unicode code point, `end_char` loại trừ. UI JavaScript cần đổi sang UTF16 khi cần.
`word_count` và `overall_band` do tools tính. JSON Schema: `WritingAssessment.model_json_schema()`.

Khi lỗi, không có `assessment`:

```json
{"status":"error","run_id":"00000000-0000-4000-8000-000000000002","code":"ASSESSMENT_VALIDATION_FAILED","retry_count":2,"errors":[{"code":"evidence_invalid","criterion":"task_response"}],"diagnostics":null}
```

`diagnostics` có thể chứa `http_status`, `provider_code`, `request_id`, `retry_after_seconds`,
`failure_kind`. Graph còn trả `trace` riêng; frontend nhận `result` đã serialize.

## 3. Hàm và dữ liệu cần từ Người 2

```python
retrieve_descriptors(task_type: TaskType, criterion: Criterion,
                     top_k: int = 3) -> list[DescriptorChunk]
```

Mỗi chunk có 7 trường: `chunk_id`, `test_part`, `criterion`, `band`, `version`, `source_url`, `text`.
Trả 1–3 chunks đúng Task/criterion; ID không trùng trong lượt chấm. `chunk_id`/`version` hiện giới hạn
`[A-Za-z0-9_.:-]{1,100}`; `band` nhận số hữu hạn 0–9. `descriptor_refs` dùng đúng các `chunk_id` này.
Schema Pydantic đã được đồng bộ vào skill writing-assessment; examiner nạp instructions.md và trace ghi tên/version skill. Xem team_integration.md để biết adapter và dữ liệu còn thiếu.
Rỗng/sai Task/criterion: trả lỗi và dừng với `RETRIEVAL_INVALID`, không chấm bằng rubric tự bịa.
Descriptor dùng đúng mức band có trong nguồn; không tự tạo descriptor 6.5 bằng nội suy.

## 4. Hàm và dữ liệu cần từ Người 4

```python
count_words(essay: str) -> int
compute_band(bands: list[float]) -> float  # 4 điểm tiêu chí
check_plagiarism(essay: str) -> PlagiarismResult
quote_validator(assessment: WritingAssessment, essay: str) -> list[ValidationIssue]
refs_validator(assessment: WritingAssessment, chunks: list[DescriptorChunk]) -> list[ValidationIssue]
consistency_validator(assessment: WritingAssessment, *, word_count: int,
    overall_band: float, plagiarism: PlagiarismResult,
    security: SecurityResult, off_topic: bool) -> list[ValidationIssue]
inspect(submission: WritingSubmission, task: ResolvedWritingTask,
        chunks: list[DescriptorChunk]) -> SecurityResult
```

`inspect` thuộc `SecurityGuard`. Interfaces hiện gọi đồng bộ.

| Kiểu trả về | Cấu trúc |
|---|---|
| `PlagiarismResult` | `possible_plagiarism: bool`, `max_similarity: float` trong 0–1, `matches: list` |
| Mỗi plagiarism match | `source_id`, `evidence: {quote, start_char, end_char}` |
| `SecurityResult` | `injection_detected: bool` |
| `ValidationIssue` | `code`, `criterion` (enum hoặc `null`) |

Validator trả `[]` khi đạt; code lỗi: `schema_invalid`, `evidence_missing`, `evidence_invalid`,
`refs_invalid`, `consistency_error`. Đây là lỗi kiểm chứng, không phải `assessment.flags`.
Thiếu/rỗng evidence bị Pydantic bắt trước validator → `schema_invalid`; `evidence_missing`
dành cho lỗi do validator N4 trả. Cả hai đều đi vào cùng vòng repair; không nới schema.
Core điều khiển retry, tối đa 3 lần sinh. Tools lỗi vận hành trả `DependencyFailure` và dừng.

## 5. Quy tắc điểm và xử lý đã chốt

- **Cập nhật 26/10: `compute_band` gọi hàm TV4, trung bình rồi làm tròn 0.5, hòa thì lên theo quy ước repository.** Ví dụ `[6,6,6,7]` → `6.5`. Quyết định raw mean cũ đã được thay trong adapter tích hợp.
  Bốn tiêu chí có trọng số bằng nhau. Quy tắc `.25/.75` công bố cho tổng bốn kỹ năng không được
  tự suy rộng sang từng Task; đây là lựa chọn tính toán của dự án dựa trên thông tin công khai.
  [Nguồn IELTS về cách tính điểm](https://ielts.org/take-a-test/your-results/ielts-scoring-in-detail).
- **`overall_band` ở đây chỉ là ước lượng một Task**, giữ tên theo đề gốc. Điểm Writing cả hai Task
  cần xét trọng số Task2 gấp đôi Task1; core này chưa tổng hợp hai bài.
  [Nguồn IELTS về bài thi Academic Writing](https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-writing).
- **Độ dài:** Task1 <150, Task2 <250 → `under_length`. Không tự trừ cố định 0.5/1 band hoặc ép
  band tổng chỉ từ số từ; cần đánh giá theo descriptor. Regex đếm từ là quy ước ứng dụng của N4/N5,
  không khẳng định là thuật toán đếm của kỳ thi thật.
  [Nguồn IELTS về độ dài bài](https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-writing).
- **Lạc đề:** giữ cờ và trần tiêu chí đầu ≤5 theo đồ án; không gán cứng 5 và không hạ tất cả tiêu chí
  về cùng điểm. Điểm thực tế vẫn phải căn cứ descriptor, có thể thấp hơn nhiều. Task1 mở rộng trần
  Achievement là policy nhóm. Bài ≤20 từ có mô tả Band1 trong descriptor; MOCK chưa thực thi chính sách
  này, không dùng kết quả MOCK để kết luận chất lượng chấm.
  [Nguồn band descriptors chính thức](https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf).
- **Plagiarism:** ngưỡng similarity là tham số do N4 kiểm chứng trên corpus; không tự đặt ngưỡng phổ
  quát hoặc suy ra “gian lận chắc chắn” từ similarity. Giữ `possible_plagiarism` và bằng chứng đoạn trùng.
- **Hợp đồng nối module:** giữ nguyên các tên hàm/DTO ở trên. `item_id` resolve từ bank có nguồn/license;
  Task1 cần material bảng/biểu đồ đã kiểm chứng. Module async/khác shape được bọc bằng adapter.
- **Trace:** metadata, ID và mã lỗi; không raw essay/secret. Usage thiếu và chi phí chưa tính là `null`,
  không phải 0. Skill invocation/version dữ liệu và kết quả tool đã che còn chờ tích hợp thật; trace mẫu
  bàn giao dự kiến `traces/samples/`, trace tạm vẫn `artifacts/traces/`.
