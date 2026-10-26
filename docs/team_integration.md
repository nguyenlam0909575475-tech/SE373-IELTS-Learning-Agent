# Tích hợp TV1/TV2/TV3/TV4/TV5

Cập nhật 26/10/2026; thay hướng dẫn adapter raw mean trong bản trước.

## Luồng hiện tại

`backend.live_service.run_live_assessment` -> `build_team_dependencies` -> graph TV3.
Graph gọi tools TV4 trước, retriever TV2 theo đúng Task/criterion, security guard,
examiner, rồi validators của skill. Thành công mới được chuyển sang schema API frontend cũ.
Chế độ live không lấy dependency từ `make_mock_dependencies`.

- Corpus mặc định: `data/corpus_plagiarism/corpus.jsonl`, đã có đủ 1.800 bài.
- Chroma: `data/chroma_db`, collection `writing_descriptors`; phải rebuild theo TV2.
- Công thức điểm duy nhất: `agent.tools.compute_tool.compute_band`, làm tròn 0.5 hòa lên theo quy ước repo.
- Canonical criterion: `coherence_cohesion`, `grammatical_range_accuracy`; boundary cũ vẫn nhận tên `_and_`.
- Public tasks nhận `source=public`, `source_url=https://...`, không bắt buộc license.
- Đề nhập qua web không có URL dùng `source=user_provided`; không tự gán self_written/CC0.

## Composition cho host khác

```python
from src.agent.graph import build_graph
from src.agent.team_adapters import MappingTaskBank, build_team_dependencies

# tasks: mapping item_id -> ResolvedWritingTask hoặc dict đã xác minh bởi host.
# examiner: instance thực hoặc examiner kiểm soát trong test.
bank = MappingTaskBank(tasks)
deps = build_team_dependencies(task_bank=bank, examiner=examiner)
graph = build_graph(dependencies=deps)
output = graph.invoke({"request": submission})
```

`submission` chỉ gồm `item_id`, `task_type`, `essay`; không đưa scores/feedback/expected vào input chấm.
Có thể truyền checker/retriever đã chuẩn bị bằng `plagiarism_checker=...`, `retriever=...`.
API frontend dùng wrapper riêng để ghép đề do người dùng cung cấp vào TaskBank của lượt chấm.
Task 1 cần số liệu biểu đồ thật trong `task_material_text`; đường dẫn ảnh đơn thuần chưa đủ.

## Runner TV5

Đọc `case_id`/`id`, `exam_question`, `scores.overall_band` của TV1, giữ tương thích dữ liệu demo.
Mặc định dùng dev; chỉ định file test để chạy hold-out. Không dùng `scores=null` làm điểm 0.
Các flags, trần tiêu chí và correction mong đợi được kiểm tra theo `expected`.
Lỗi live được ghi lại theo bài, có đếm số thành công/thất bại; không tạo điểm thay thế.
Report refs của runner chỉ kiểm tra lẫn Task theo tên; graph live mới kiểm tra membership đầy đủ.

## Phần cần cấu hình trước khi chạy live

1. Cài requirements.txt, gồm SDK openai cho provider OpenAI-compatible hiện có.
2. Rebuild ChromaDB từ JSON descriptors TV1 bằng scripts/rebuild_vectorstore.py.
3. Cấu hình API key/base URL/model cùng provider theo .env.example.
4. Cung cấp số liệu biểu đồ chính xác cho Task 1, hoặc xây adapter thị giác ở TV3/TV5.
5. Hiệu chỉnh ngưỡng đạo văn trên dev có nhãn rồi đo test riêng; benchmark điểm IELTS không thay tập này.

Band 0 policy vẫn là kênh riêng của TV2, không tự tạo chunk_id hoặc tự cho Band 0 vì thiếu từ/đạo văn.
Các bài kiểm thử offline không chứng minh chất lượng chấm của LLM hay chất lượng semantic retrieval.
