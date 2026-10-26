# Contracts Người 3 — đề xuất kỹ thuật tích hợp

**[GỐC]** SSOT public assessment duy nhất: `src.agent.schemas.WritingAssessment` (Pydantic v2,
extra='forbid', revalidate_instances='always'). Không duy trì JSON schema viết tay song song;
N2/N5 gọi `WritingAssessment.model_json_schema()` khi cần schema.

| Field [GỐC] | Kiểu / điều kiện |
|---|---|
| task_type | task1/task2 |
| word_count | integer ≥0, chỉ từ N4 count_words |
| criteria | đúng 4; criterion, band, evidence, descriptor_refs, comment |
| overall_band | số hữu hạn, chỉ từ N4 compute_band trên 4 band |
| corrections | original, suggestion, reason, category=grammar/lexis/cohesion/task |
| flags | list enum under_length/off_topic/possible_plagiarism/injection_detected |
| disclaimer | câu tiếng Việt đầy đủ đã ghi trong prompt |

**[NHÓM]** Task1: task_achievement/coherence_cohesion/lexical_resource/grammatical_range_accuracy.
Task2 thay task_achievement bằng task_response. Không trùng/thiếu/sai Task. Các string phải có
nội dung. Quote không trim/normalize. Evidence và refs không rỗng cho mỗi criterion.
**[ĐỀ XUẤT]** Band là số hữu hạn [0,9], không ép bước 0.5 hay số nguyên; đây là giới hạn
kỹ thuật nhóm cần xác nhận, không phải mô tả thuật toán chấm hay scale descriptor gốc.
Descriptor band giữ numeric; nhóm N1 dự kiến integer1–9 cho corpus thật, chưa ép lên score model.

## Input và state [ĐỀ XUẤT]

`WritingSubmission(item_id, task_type, essay)` là input duy nhất. Browser gửi task_prompt
hay bất kỳ field thừa nào đều INVALID_INPUT. Đề resolve theo item_id từ TaskBank.
`ResolvedWritingTask`: item_id/task_type/task_prompt, task_material_text optional,
source (self_written/llm_generated_verified/open_license/public/user_provided).
Nguồn public cần source_url HTTPS; license có thể null. Các kiểu nguồn cũ vẫn cần license
đã khai báo; user_provided không tự nhận quyền sở hữu hoặc giấy phép cho đề người dùng nhập.
**[CẬP NHẬT 26/10]** source bắt buộc; license theo loại nguồn ở trên. **[ĐỀ XUẤT]** Trong harness text-only, Task1 thiếu material
sẽ INVALID_TASK: cần dữ liệu bảng/biểu đồ để đánh giá Task Achievement. N1 quản lý toàn bộ
metadata bank theo §2.1 và xác minh quyền sử dụng; graph chỉ kiểm tra DTO tối thiểu, không tự
xác nhận license bất kỳ là hợp pháp.

AgentState là TypedDict riêng gồm request/submission/resolved_task/retrieved_chunks/word_count/
plagiarism_result/security_result/grading_draft/validation_errors/attempt_count/run_id/candidate/
error_code/result/trace. Không dùng làm API payload. GraphInput chỉ nhận request;
GraphOutput chỉ xuất result+trace, không trả raw request/draft cho frontend.

## N2 → N3 [NHÓM signature; GỐC tên/filter]

```python
retrieve_descriptors(task_type: TaskType, criterion: Criterion,
                     top_k: int = 3) -> list[DescriptorChunk]
```

DescriptorChunk gồm chunk_id/test_part/criterion/band/version/source_url/text.
Mỗi criterion gọi riêng, 1–3 chunks; rỗng, quá giới hạn, metadata sai, ID trùng toàn run,
source_url thiếu/sai format → RETRIEVAL_INVALID, không gọi examiner.
**[ĐỀ XUẤT]** IDs/version dùng `[A-Za-z0-9_.:-]{1,100}` để trace không nhận văn bản tuỳ ý.
source_url nhận http(s), riêng fixtures dùng `mock://`; kiểm URL chỉ là cấu trúc, không tải URL.
Refs phải khớp ID **và** Task **và** criterion ở manifest hiện tại; không dùng cache run trước.
N1/N2 phải xác minh provenance/allowlist nguồn thật khi thay MOCK.

## N4 → N3 [GỐC tên; ĐỀ XUẤT signature/return]

```python
count_words(essay: str) -> int
compute_band(bands: list[float]) -> float  # exactly four bands
check_plagiarism(essay: str) -> PlagiarismResult
quote_validator(assessment: WritingAssessment, essay: str) -> list[ValidationIssue]
refs_validator(assessment: WritingAssessment, chunks: list[DescriptorChunk]) -> list[ValidationIssue]
consistency_validator(assessment, *, word_count, overall_band,
                      plagiarism, security, off_topic) -> list[ValidationIssue]
SecurityGuard.inspect(submission, task, chunks) -> SecurityResult
```

PlagiarismResult: possible_plagiarism(bool), max_similarity(float0–1),
matches=[{source_id, evidence:{quote,start_char,end_char}}]. Tên max_similarity/matches là
**[ĐỀ XUẤT]**; nguồn gốc chỉ yêu cầu similarity và đoạn trùng. Fake trả false/0/[] cố định,
không chạy đối chiếu corpus. Ngưỡng/thuật toán do N4 xác nhận.
SecurityResult: injection_detected(bool), fake substring guard không phải semantic defence.
Các lỗi tool/validator hoặc DTO dependency không hợp lệ → DEPENDENCY_UNAVAILABLE, không repair.
Nếu module cũ chỉ có compute_task_band, N4 viết adapter expose compute_band,
ví dụ method compute_band(self,bands): return legacy.compute_task_band(bands).
Core không export tên cũ vì chưa có module production cần tương thích.

ValidationIssue: `{code, criterion:null|enum}`; không echo raw input/exception.
Codes nội bộ: schema_invalid/evidence_missing/evidence_invalid/refs_invalid/consistency_error.
Schemas bắt evidence rỗng thành schema_invalid trước validator; evidence_missing được dành
cho adapter N4 hoặc output chưa parse. N4 validators không được chấp nhận dữ liệu sai chỉ
để hoàn tất workflow. overall_band là kết quả tool, validator kiểm consistency với kết quả đó;
kiểm công thức/rounding thuộc unit tests tool N4, không gọi tool lại để tự đoán quy tắc.

**[NHÓM]** regex mock dùng `\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b` từ phân công.
**[CHƯA CHỐT]** Đây không phải tiêu chuẩn đếm từ IELTS được xác minh; N4/N5 thống nhất Unicode,
hyphen, apostrophe, số. **[CẬP NHẬT 26/10]** compute_band dùng hàm N4 trong
agent/tools/compute_tool.py, trung bình bốn tiêu chí rồi làm tròn gần nhất 0.5, hòa thì lên.
Ví dụ [6,6,6,7] -> 6.5. Đây là quy ước repository theo AGENTS.md/phân công và tests,
không phải khẳng định quy tắc điểm Task chính thức. Adapter không giữ công thức raw mean riêng.

## Examiner và flags [ĐỀ XUẤT]

Examiner.generate(ExaminerInput) -> object, được parse bằng LLMGradingDraft.
Input chứa submission, task, chunks, validation_errors, attempt(1..3). Tất cả text là DATA.
Draft chỉ có criteria/corrections/off_topic, cấm word_count/overall_band/flags.
Fake score cố định6, hoặc first criterion5 cho fixture off_topic; không đọc chỉ dẫn trong essay.
Code assemble under_length từ tool count, plagiarism/security từ tool, off_topic từ draft.
**[GỐC]** Task2 off_topic → response≤5. **[NHÓM]** mở rộng Task1 achievement≤5.

## Retry/error/API [ĐỀ XUẤT]

build_graph(dependencies=Dependencies(...)) trả compiled StateGraph thật.
`graph.invoke({"request": submission_json})` → `{result: AgentSuccess|AgentError, trace: [...]}`.
N5 chỉ serialize result bằng `model_dump(mode="json")` hoặc `model_dump_json()`.
Success: status/run_id/assessment. Error: status/run_id/code/retry_count/errors, không assessment.
Mỗi invoke reset UUID run_id và attempt_count, không chia sẻ state/checkpointer/cached grade.
Schema/quote/ref/consistency của draft sửa được → tối đa 2 retry, tổng3 generations.
Unknown item/task mismatch/input/retrieval/dependency hỏng → dừng ngay, không retry examiner.
Không có backoff/retry hạ tầng ngầm. N5 quyết định HTTP status; core không phụ thuộc FastAPI.

## Unicode, trace và privacy [ĐỀ XUẤT]

Offsets là Python Unicode code points `[start_char:end_char)`, end-exclusive, trên essay nguyên văn.
N5 convert khi JS dùng UTF16; ví dụ JS: `Array.from(essay).slice(start,end).join('')`
để lấy quote; index UTF16 là `Array.from(essay).slice(0,start).join('').length`.
Không áp thẳng codepoint offsets cho String.slice UTF16 khi có emoji/surrogate pairs.

TraceEvent allowlist: run_id/node/kind/start/end/duration/attempt/codes/chunk IDs/versions/model/
prompt version, usage/cost=null. Từng tool event có tên, latency, trạng thái lỗi và manifest;
không dump args/results raw. N3 không bật cloud tracing/checkpointer hoặc ghi file ngầm.
JSONL export là explicit và demo synthetic bị ignore. Không raw essay/task prompt/chunk text,
exception message/Pydantic.errors() hay chain-of-thought. Unknown upstream exceptions bị
sanitise thành code; debug production cần N4 thiết kế phân loại lỗi an toàn.


## Nhánh thử Gemini [ĐỀ XUẤT / USER AUTHORIZED]

`experiment/person3-gemini` có optional GeminiExaminer; xem live_llm.md. WritingAssessment
không thay đổi. Examiner có thể thêm property last_usage: ExaminerUsage(input_tokens,output_tokens)
để graph bổ sung token metadata thực vào trace. Fakes không có telemetry vẫn để null.
ErrorCode thêm nhóm LLM_* cho cấu hình, auth/model/quota/timeout/request/blocked/truncated/empty;
đây là lỗi dependency không repair. SDK HTTP attempts=1, chỉ graph điều khiển schema-repair.


## Diagnostics provider và repair JSON [ĐỀ XUẤT]

AgentError có diagnostics: ProviderDiagnostics|null. TraceEvent có provider_diagnostics cùng DTO.
DTO chỉ gồm http_status, provider_code allowlist, request_id bounded req_ format, failure_kind.
Không thay WritingAssessment. Raw exception/provider body/message/failed_generation không lưu
hoặc phản hồi. CLI liệt kê diagnostics theo attempt để lần sửa thành công vẫn truy được lỗi đầu.
HTTP400 + code json_validate_failed chính xác là DraftGenerationFailure: node examiner chuyển
thành schema_invalid và dùng chung giới hạn tổng3 lần sinh. Không retry request400 khác hoặc
HTTP auth/quota/5xx. Lỗi provider JSON hết budget trả ASSESSMENT_VALIDATION_FAILED kèm diagnostics.

`diagnostics.retry_after_seconds` là số giây từ Retry-After, chỉ nhận số hữu hạn trong 0–86400; thiếu/không hợp lệ là null. HTTP 429 không tự retry.
