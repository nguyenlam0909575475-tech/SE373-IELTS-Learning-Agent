# Member 1 → Member 4: corpus đối chiếu đạo văn

## Dữ liệu bàn giao

`data/corpus_plagiarism/corpus.jsonl` có **1.800 bài**: 600 Academic Task 1 và 1.200 Task 2 dạng essay. [Manifest](../data/corpus_plagiarism/manifest.json) ghi nguồn, commit dữ liệu, hash và số lượng; [corpus README](../data/corpus_plagiarism/README.md) ghi cách tạo lại.

Nguồn public là [hai2131/IELTS-essays-task-1](https://huggingface.co/datasets/hai2131/IELTS-essays-task-1) và [chillies/ielts-writing-task2-essays](https://huggingface.co/datasets/chillies/ielts-writing-task2-essays). Corpus giữ bài gốc và lỗi gốc, loại bản trùng chuẩn hóa, thư và bài quá ngắn; không lấy điểm band hoặc feedback làm nhãn. Không trùng nguyên văn chuẩn hóa với 84 bài benchmark và 6 basic cases.

Mỗi dòng JSON có đúng **6 trường**:

| Trường | Cách sử dụng |
| --- | --- |
| `source_id` | ID duy nhất; trả lại trong `matches` |
| `task_type` | `task1` / `task2`; ngữ cảnh tham chiếu |
| `exam_question` | Đề bài; không ghép vào văn bản so khớp |
| `text` | Toàn văn dùng để tìm đoạn trùng |
| `topic` | Chủ đề / dạng biểu đồ |
| `source_url` | URL public tới dòng nguồn |

Không có trường `license`; quy định hiện hành chỉ yêu cầu nguồn public. Corpus không cần nhãn band vì không dùng đo độ chính xác chấm IELTS. Task 1 không cần ảnh cho phép so khớp văn bản này.

## Member 4 cần điều chỉnh

Đối chiếu code hiện tại ở `agent/tools/plagiarism_tool.py`:

1. `CorpusEntry`/loader không được bắt buộc `license`. Không tự điền giấy phép giả để vượt validation.
2. Loader hiện dùng `CorpusEntry(**record)`, sẽ lỗi với metadata bổ sung. Chọn các trường so khớp `source_id`, `text`, `source_url`; cho phép đọc ba metadata còn lại mà không ép đổi file Member 1.
3. Đổi đường dẫn corpus mặc định từ danh sách link `data/knowledge/sample_corpus_links.json` sang `data/corpus_plagiarism/corpus.jsonl`, hoặc truyền đường dẫn này khi khởi tạo dependency.
4. Khởi tạo chỉ mục một lần và tái sử dụng checker cho các request; không nạp 1.800 bài lại ở mỗi lần chấm.
5. Giữ xử lý lỗi thiếu/hỏng corpus; không trả `similarity=0` như thể đã đối chiếu thành công.

Sau khi điều chỉnh loader, API hiện có được dùng như sau:

```python
from agent.tools.plagiarism_tool import PlagiarismChecker

checker = PlagiarismChecker.from_jsonl("data/corpus_plagiarism/corpus.jsonl")
result = checker.check_plagiarism(essay)
```

Đây là hướng dẫn cho loader sau khi Member 4 cập nhật; loader ở `main` trước PR dữ liệu vẫn có hai ràng buộc cũ ở mục 1–2. Member 1 không sửa thuật toán hoặc DTO của Member 4 trong PR này.

## Kiểm tra tiếp nhận

```powershell
python scripts/check_member1_data.py
```

Sau khi nối loader, Member 4 kiểm tra:

- Nạp đủ 1.800 ID không trùng, không sửa văn bản corpus.
- Lấy nguyên một `text` làm đầu vào: độ phủ nguồn tương ứng bằng 1; có cờ theo ngưỡng cấu hình.
- Đoạn chứng cứ phải khớp chính xác `essay[start_char:end_char]`; `source_id` truy được về URL trong corpus.
- Bài rỗng/ngắn, file không tồn tại, JSON lỗi và ID trùng có xử lý đúng hợp đồng.
- Không coi đoạn chung của đề hoặc cụm mở bài ngắn là kết luận chắc chắn đạo văn.

Các phép thử trên kiểm tra tích hợp, không chứng minh tỷ lệ phát hiện ≥90% / gắn nhầm ≤10%. Member 4 phối hợp Member 5 xây tập bài chép và bài tự viết có nhãn riêng, hiệu chỉnh ngưỡng trên dev rồi đo trên test. Thuật toán n-gram có hạn chế với paraphrase và bài ghép nhiều nguồn.
