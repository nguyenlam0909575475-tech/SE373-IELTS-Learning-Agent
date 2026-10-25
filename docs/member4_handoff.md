# Bàn giao N4 trong SE373-Agent

Cập nhật: 25/10/2026. N4 tiếp tục phụ trách tools theo phân công đã xác nhận.
Code được chuyển từ repo SE373 cũ sang nhánh `feature/m4-tools` của repo thử nghiệm.
Repo cũ được giữ nguyên. Chưa commit hoặc push phần chuyển code này.

## 1. Code đã được đặt ở đâu?

| File trong repo mới | Công việc |
| --- | --- |
| `agent/tools/compute_tool.py` | `count_words`, `compute_band`, tên tương thích `compute_task_band` |
| `agent/tools/plagiarism_tool.py` | Đọc kho bài mẫu và so sánh các cụm từ liên tiếp |
| `agent/tools/security_tool.py` | `SecurityGuard.inspect` phát hiện một số mẫu chỉ dẫn đáng ngờ |
| `agent/tools/contracts.py` | Các kiểu kết quả tool, lỗi kiểm tra, lỗi thiếu dữ liệu |
| `skills/writing_assessment/validators.py` | Kiểm tra trích dẫn, tham chiếu tiêu chí và sự nhất quán của kết quả |
| `skills/writing_assessment/checks.py` | Giữ schema N3, gọi các hàm N4 để kiểm tra kết quả AI |
| `tests/` và `evals/member4_security_cases.json` | Kiểm thử bằng dữ liệu tự soạn, gồm ca kiểm tra ghép với N3 |
| `scripts/check_repository.py`, `.githooks/` | Kiểm tra file riêng tư, file sinh tự động và mẫu khóa bí mật trước commit/push |

Code sử dụng cấu trúc sẵn có của repo mới. Các lớp adapter/factory của repo cũ không được chép sang,
vì repo mới sử dụng trực tiếp schema Pydantic và `validate_writing_assessment` của N3.
Các file backend, agent loop, RAG và dữ liệu chưa hoàn thành không được tự điền dữ liệu giả.

## 2. N4 đã ghép với N3 như thế nào?

Schema chính vẫn là `WritingAssessment` trong `skills/writing_assessment/checks.py`.
N4 đã dùng đúng tên tiêu chí của N3:

- Task 1: `task_achievement`; Task 2: `task_response`.
- Cả hai Task: `coherence_and_cohesion`, `lexical_resource`, `grammatical_range_and_accuracy`.

Các tên có `_and_` khác bản bàn giao ở repo cũ. Tool và kiểm thử đã được đổi theo tên trong repo mới.
N3 vẫn gọi được `compute_ielts_overall_band`; hàm này chuyển tiếp sang `compute_band` của N4.
Như vậy, bộ kiểm tra và hội đồng chấm cùng dùng một cách tính điểm.
Hàm sửa vị trí trích dẫn `repair_evidence_offsets` của N3 được giữ nguyên; bộ kiểm tra không tự gọi hàm sửa này.

### Chính sách tính điểm hiện đang áp dụng

`compute_band([6, 6, 6, 7])` trả về **6.5**. Trung bình trước khi làm tròn là 6.25.
`compute_band([6, 7, 7, 7])` trả về **7.0**. Trung bình trước khi làm tròn là 6.75.
Hàm không làm tròn riêng từng đầu vào. Schema N3 yêu cầu band tiêu chí nằm trong 1.0–9.0, bước 0.5;
tool tính toán nhận bốn số hữu hạn trong 0–9, còn kiểm tra schema áp dụng giới hạn chặt hơn của N3.

Đây là chính sách đang được code và kiểm thử N3 trong repo mới yêu cầu, khác bản N4 cũ giữ nguyên trung bình.
Tài liệu này không khẳng định quy tắc làm tròn điểm Task là quy định chính thức của IELTS.
Hàm này chưa tính điểm Writing kết hợp hai Task và chưa tính Overall của bốn kỹ năng.

## 3. Thứ tự các phần cần gọi

1. Agent nhận bài viết nguyên bản và đề bài.
2. Trước khi AI chấm, agent gọi `count_words`, công cụ so bài mẫu và `SecurityGuard.inspect`.
3. Bộ RAG cung cấp các đoạn tiêu chí đúng Task. AI dùng các đoạn đó để chấm bốn tiêu chí và trích dẫn bài viết.
4. Sau khi AI trả kết quả, code gọi `compute_band` từ bốn band tiêu chí để tạo điểm Task.
5. Agent gọi `validate_writing_assessment` với kết quả AI và kết quả tool đã tính độc lập.
6. Nếu `passed` là `False`, agent xử lý các lỗi hoặc yêu cầu sửa theo cơ chế retry của nhóm.
   Agent không hiển thị kết quả như một bài chấm hợp lệ khi kiểm tra chưa qua.

N4 không tự xác định bài có lạc đề hay không. Agent/phần chấm ngữ nghĩa phải cung cấp tín hiệu `off_topic`;
N4 đối chiếu cờ và kiểm tra giới hạn điểm TA/TR tối đa 5.0 theo yêu cầu dự án.

Đoạn dưới minh họa cách kiểm tra sau khi đã có bài, kết quả AI, các đoạn RAG và kết quả cảm biến:

```python
from agent.tools.compute_tool import count_words
from skills.writing_assessment.checks import validate_writing_assessment

result = validate_writing_assessment(
    raw_output,
    essay_text,
    expected_task_type=task_type,
    expected_word_count=count_words(essay_text),
    retrieved_descriptors=chunks,
    plagiarism_result=plagiarism,
    security_result=security,
    off_topic=off_topic_result,
)
if not result.passed:
    # Chuyển result.errors sang cơ chế sửa lỗi/retry của agent.
    # Không ghi toàn bộ bài viết hoặc khóa bí mật vào log.
    ...
```

Các biến trong ví dụ phải do agent cung cấp; đây không phải lệnh chạy toàn bộ ứng dụng.
Các tham số cũ của N3 vẫn dùng được, bao gồm `retrieved_descriptor_ids`.
Tuy nhiên, chỉ truyền danh sách ID thì không đủ kiểm tra metadata của tiêu chí;
agent cần truyền `retrieved_descriptors` đầy đủ như ví dụ.
Nếu bỏ `expected_word_count`, chế độ tương thích cũ không đối chiếu với số từ thực tế của bài.
Nếu bỏ một kết quả cảm biến hoặc truyền `None`, tín hiệu đó chưa được xác minh, không được coi là âm tính.

## 4. Định dạng N4 đang đọc

Một đoạn tiêu chí RAG cần có đủ bảy trường dưới đây. Đây chỉ là mẫu tự soạn cho kiểm thử, không phải rubric IELTS:

```json
{
  "chunk_id": "MOCK_task2_task_response_6",
  "test_part": "task2",
  "criterion": "task_response",
  "band": 6.0,
  "text": "Synthetic descriptor placeholder, not an IELTS rubric.",
  "source_url": "urn:se373:synthetic-test",
  "version": "SYNTHETIC_v1"
}
```

Trong kết quả AI, tiêu chí `task_response` có thể dẫn `descriptor_refs: ["MOCK_task2_task_response_6"]`
nếu đoạn này thực sự nằm trong danh sách RAG đã cung cấp ở lần chạy đó.
ID phải duy nhất, đúng Task, đúng tiêu chí; ID và version dài 1–100 ký tự, chỉ dùng chữ, số, `_`, `.`, `:`, `-`.
Danh sách truyền vào validator cần được lọc đúng Task; metadata còn phải có band hợp lệ và nội dung/nguồn không rỗng.
`source_url` và `version` đã được bổ sung vào hợp đồng trong `skill.yaml` để hai phần dùng cùng định dạng.

Kho bài mẫu mặc định nằm ở `data/knowledge/sample_corpus_links.json`.
Loader nhận một mảng JSON; mỗi phần tử có `source_id`, `text`, `source_url`, `license`.
Ví dụ về hình dạng một phần tử, chưa phải nội dung bài mẫu để sử dụng:

```json
{
  "source_id": "source_001",
  "text": "Nội dung đầy đủ của bài mẫu được phép sử dụng phải được đặt ở đây.",
  "source_url": "Đường dẫn hoặc định danh nguồn",
  "license": "Giấy phép hoặc căn cứ được phép sử dụng"
}
```

Tool cần nội dung bài để so sánh; danh sách URL đơn thuần không đủ.
`PlagiarismChecker.from_file(path)` đọc mảng JSON hoặc đọc JSONL khi tên file có đuôi `.jsonl`.
Agent có thể khởi tạo một checker rồi sử dụng lại `checker.check_plagiarism(essay)` cho nhiều yêu cầu.
Tool không tự tải bài trên Internet. Loader chỉ kiểm tra sự hiện diện/kiểu dữ liệu của metadata;
nhóm vẫn phải xác minh quyền sử dụng nguồn trước khi đưa dữ liệu vào kho.

Kết quả so sánh có `possible_plagiarism`, `max_similarity`, `matches`.
Mỗi phần tử `matches` có `source_id` và `evidence` với `quote`, `start_char`, `end_char`.
Kết quả bảo mật có `injection_detected`.
Các kết quả này là dataclass, có thể chuyển sang dict bằng `dataclasses.asdict`.

## 5. Khi kiểm tra báo lỗi

Một lỗi N4 có `code`, `criterion`, `reason`, `path`.
`checks.py` chuyển lỗi này thành chuỗi trong `ValidationResult.errors`, giữ kiểu trả về cũ của N3.
Ví dụ:

```text
evidence_invalid at criteria[0].evidence[0]: quote not found verbatim in essay
evidence_invalid at criteria[1].evidence[0]: char offset does not match the quote
```

Lỗi đầu nói câu trích dẫn không tồn tại nguyên văn. Lỗi sau nói vị trí ký tự không khớp câu trích dẫn.
`path` dùng chỉ số bắt đầu từ 0 để chỉ đúng phần tử sai; thông báo không chép bài viết vào lỗi.
`refs_invalid` nói dữ liệu RAG hoặc tham chiếu không hợp lệ.
`consistency_error` kèm lý do cụ thể khi số từ, điểm hoặc cờ không khớp kết quả tin cậy.
`schema_invalid` nói cấu trúc/kiểu dữ liệu không phù hợp để kiểm tra.

Nếu chưa có kho bài mẫu, tool ném `Member4DependencyError` có mã `PLAGIARISM_CORPUS_MISSING`.
File rỗng, dữ liệu sai, thiếu nội dung/nguồn/giấy phép có thể báo `PLAGIARISM_CORPUS_INVALID`.
Đây là lỗi dữ liệu đầu vào cần xử lý; agent không được thay bằng `possible_plagiarism=False` để tiếp tục như đã kiểm tra.

## 6. Giới hạn còn giữ từ bản cũ

- Regex đếm từ hiện là `\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b`.
  `don't` và `state-of-the-art` mỗi từ tính một; dấu nháy cong, chữ có dấu và số thập phân chưa được xử lý đầy đủ.
  Frontend cần dùng cùng quy ước hoặc hiển thị số đếm từ backend. Chưa thể khẳng định hai phía đã đồng bộ vì frontend còn rỗng.
- So bài chép dùng cụm năm từ liên tiếp, mặc định phủ ít nhất 80% số token của bài và có ít nhất 20 từ khớp với một nguồn.
  Đây là ngưỡng thử nghiệm chưa hiệu chỉnh bằng benchmark. Sửa từ rải rác có thể phá vỡ các cụm năm từ và làm tool bỏ sót.
  Cờ chỉ gợi ý cần xem lại; không chứng minh đạo văn và không tìm kiếm toàn Internet.
- Guard dùng mẫu chuỗi để phát hiện một số dạng prompt injection; nó chưa bảo đảm chặn mọi cách tấn công.
  Agent vẫn phải cách ly nội dung bài làm và không thực thi chỉ dẫn bên trong dữ liệu không tin cậy.
- Unit test sử dụng bài và điểm giả lập tự soạn. Các điểm này không phải nhãn chuẩn và không dùng để báo độ chính xác UC-08.

## 7. Còn cần nhận gì để chạy toàn bộ?

- Kho bài mẫu có nội dung và nguồn/giấy phép hợp lệ; file mặc định hiện vẫn rỗng.
- Các đoạn rubric và công cụ RAG thật, theo metadata ở trên.
- Agent loop/backend để gọi tools, gọi AI, truyền kết quả kiểm tra và thực hiện retry; các file này hiện còn rỗng.
- Kiểm thử với mô hình thật và bộ bài có điểm chuẩn hợp lệ khi nhóm đã ghép ứng dụng.

N4 đã ghép và kiểm thử với schema, checks và committee hiện có của N3 bằng dữ liệu giả lập.
Điều này chưa đồng nghĩa toàn bộ ứng dụng hoặc chất lượng chấm điểm đã được xác nhận.

## 8. Cách tự kiểm tra lại

Sau khi đã kích hoạt `.venv` và cài `requirements.txt`, chạy ở gốc repo:

```bash
ruff check .
python -B -m pytest -p no:cacheprovider
python -B scripts/check_repository.py
python -B scripts/check_repository.py --history
git diff --check
```

Hook kiểm tra nội dung chuẩn bị commit và lịch sử trước push đã được bật trên máy hiện tại:
`git config core.hooksPath .githooks`. Máy khác cần tự chạy lệnh cấu hình này.
CI cũng kiểm tra file/khóa, Ruff và Pytest trên Python 3.11/3.12; chưa có lần chạy CI mới vì chưa push.
Môi trường local sử dụng Python 3.14.7. Kết quả local sau khi chuyển code: **228 kiểm thử qua**, `ruff check .` qua,
`git diff --check` qua; bộ quét worktree và lịch sử Git không phát hiện trường hợp bị chặn.
Sáu kiểm thử gốc của N3 và code `committee.py` không bị chỉnh sửa.
Lần chạy trong môi trường Codex sử dụng thư mục tạm riêng cho Pytest để tránh giới hạn quyền ghi thư mục tạm hệ thống.
Bộ quét chỉ phát hiện các mẫu phổ biến, không thay thế việc xem lại file trước commit.

## 9. Minh bạch sử dụng AI

Codex hỗ trợ chuyển code, chỉnh import/hợp đồng, nối các kiểm tra vào code N3,
viết kiểm thử và tài liệu trong lần chuyển này. Người phụ trách cần đọc và hiểu trước khi nộp.
Dữ liệu kiểm thử tự soạn được sử dụng để kiểm tra hành vi kỹ thuật; AI không gán nhãn điểm chuẩn IELTS.
