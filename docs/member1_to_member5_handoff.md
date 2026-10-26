# Member 1 → Member 5: benchmark, ảnh và basic cases

## Dữ liệu nhận bàn giao

| File | Nội dung |
| --- | --- |
| `evals/benchmark_dev/benchmark.json` | 69 bài: 21 Task 1, 48 Task 2; dùng phát triển/tune prompt |
| `evals/benchmark_test/benchmark.json` | 15 bài: 10 Task 1, 5 Task 2; giữ làm hold-out |
| `evals/materials/` | 26 ảnh đề cho 31 bài Task 1, thêm 1 biểu đồ dùng cho basic cases |
| `evals/data/5_basic_cases.json` | 6 bài cho 5 nhóm kiểm tra hành vi; `scores=null` |

Benchmark có **84 bài**, band tổng 4.0–8.0, đủ bốn điểm tiêu chí và điểm tổng. [Nguồn và phương pháp nhãn](../evals/README.md#phương-pháp-xây-dựng-nhãn) dùng điểm do các nguồn public công bố, không tự gán điểm chuẩn bằng LLM. Không đổi bài/điểm/chia tập để phù hợp đầu ra Agent.

## Ánh xạ cho runner

Benchmark có 8 trường: `case_id`, `task_type`, `exam_question`, `essay`, `material`, `scores`, `feedback`, `source`. Basic cases thay `feedback` bằng `expected`; cả sáu bài có `scores=null`.

| Dữ liệu Member 1 | Runner / adapter sử dụng |
| --- | --- |
| `case_id` | ID kết quả; `item_id` khi gửi Agent |
| `exam_question` | Đề bài; ánh xạ sang `prompt`, `topic` hoặc `task_prompt` theo API runner |
| `essay` | Bài làm gửi chấm |
| `material` | Đường dẫn ảnh theo hướng dẫn bên dưới |
| `scores.overall_band` | `ground_truth_band` nếu runner đang dùng tên này; chỉ dùng sau khi có dự đoán |
| Bốn điểm trong `scores` | Tính MAE từng tiêu chí; Task 1 dùng TA, Task 2 dùng TR |
| `expected` | Điều kiện kiểm tra hành vi của basic cases |

`evals/run.py` hiện đọc `id`, `topic`, `ground_truth_band`; cần Member 5 ánh xạ từ các tên trên, không đổi JSON Member 1 về schema cũ. Runner cần đọc đúng 69 dev / 15 test, thay bộ minh họa `writing_benchmark_30.json` khi báo cáo kết quả benchmark thật. Các giá trị enum tiêu chí có thể khác ở DTO của service: ánh xạ `coherence_and_cohesion` → `coherence_cohesion`, `grammatical_range_and_accuracy` → `grammatical_range_accuracy` khi so điểm.

Nếu chạy runner cũ ngay với basic cases mới, `id` trở thành `None` và `run_full_evaluation` lỗi ở bước phân loại under-length. Cập nhật ánh xạ `case_id` trước, rồi dùng `expected` để kiểm tra từng điều kiện; không sửa fixture hoặc bỏ test để che lỗi tích hợp này.

## Nạp ảnh Task 1

Ảnh đã có trên nhánh và không bị ignore. [Trang xem ảnh](../evals/materials/README.md) hiển thị trên GitHub; clone repo sẽ có cùng các file, không cần server `localhost`.

Benchmark dùng chuỗi `material="evals/materials/ten_anh.png"`; basic cases dùng object `material={"path": "evals/materials/...jpg", "url": "https://..."}`. Task 2 có `material=null`.

```python
from pathlib import Path

root = Path.cwd()  # Thư mục gốc repository
material = row["material"]
relative_path = material["path"] if isinstance(material, dict) else material
image_bytes = (root / relative_path).read_bytes() if relative_path else None
submission = {
    "item_id": row["case_id"],
    "task_type": row["task_type"],
    "essay": row["essay"]
}
```

Member 5 đăng ký đề và ảnh theo `case_id` trong TaskBank/adapter. Đường dẫn ảnh trong JSON không tự chuyển thành đầu vào thị giác: service/examiner phải nhận bytes/base64 hoặc nội dung bảng/biểu đồ tương đương đầy đủ. DTO `ResolvedWritingTask` hiện còn enum nguồn và `license` bắt buộc theo quy định cũ; phối hợp bên sở hữu DTO để nhận nguồn public, không gán `self_written`/CC0 cho đề public chỉ để vượt validation.

Không gửi `scores`, `feedback`, `expected` hoặc trang nguồn có đáp án vào prompt chấm. Nguồn/nhãn chỉ dùng để đối chiếu và báo cáo sau khi có dự đoán. Backend live hiện dùng dependency mock ở một số khâu; không báo cáo như đã chấm với RAG/corpus thật nếu chưa nối các dependency này.

## Năm nhóm basic cases

| ID | Số từ theo regex N4 | Điều kiện chính |
| --- | ---: | --- |
| `case_01_task1_normal` | 230 | Không `under_length` / `off_topic`; đủ bốn tiêu chí Task 1 |
| `case_02_task2_normal` | 381 | Không `under_length` / `off_topic`; đủ bốn tiêu chí Task 2 |
| `case_03a_task1_under_length` | 125 | Có `under_length` vì <150 từ |
| `case_03b_task2_under_length` | 200 | Có `under_length` vì <250 từ |
| `case_04_off_topic_advanced` | 469 | Có `off_topic`; `task_response<=5.0`, không ép giảm các tiêu chí khác |
| `case_05_grammar_errors` | 179 | Có correction `grammar` và `under_length` |

`expected.required_flags` và `expected.forbidden_flags` mặc định là `[]` khi không có. `criterion_band_max` là trần điểm; `correction_categories_contains` yêu cầu xuất hiện ít nhất một correction thuộc nhóm chỉ định. Không gán điểm 0 thay cho `scores=null` và không đưa các bài này vào mẫu số MAE.

Với mỗi kết quả thành công, kiểm tra đủ bốn tiêu chí, evidence/offset khớp bài gốc, descriptor refs đúng chunks của lượt retrieval, số từ theo tool N4, overall theo hàm tính điểm đã thống nhất. Không tự trừ cố định band vì thiếu từ. Cờ đạo văn phụ thuộc corpus; không mặc định bài public là bài tự viết không đạo văn.

Nguồn basic cases: bài Case 1/2/3a/3b từ [IELTS.org — candidate responses](https://ielts.org/cdn/computer-delivered-sample-tests-academic-writing/ielts-academic-writing-example-responses-to-parts-1-and-2-with-band-scores-and-examiner-comments.pdf); Case 5 từ trang 18 của [IELTS.org — sample tasks](https://ielts.org/cdn/Sample-tests/ielts-academic-writing-sample-tasks-2023.pdf). Case 4 là đề du lịch và bài về hoàn cảnh gia đình được cung cấp để thử lạc đề; URL trong fixture chỉ dẫn PDF có đề du lịch gốc. [Biểu đồ phương tiện đến trường](https://www.ieltsluminary.com/post/the-number-of-trips-made-by-children) đi kèm Case 1/3a; phần mô tả đề đã ghi chú hai năm vì ảnh thiếu chú giải.

## Kiểm tra trước khi chạy Agent

```powershell
python scripts/check_member1_data.py
python scripts/check_writing_benchmark.py
```

Sau khi nối service, chạy mock để kiểm tra luồng và chạy live để đo mô hình. Tune trên dev; khóa cấu hình rồi đánh giá 15 bài hold-out; khi nghiệm thu UC-02 chạy toàn bộ 84 bài và báo cáo riêng dev/test/toàn bộ. Đo MAE bốn tiêu chí và overall, tỷ lệ sai lệch ≤0.5/≤1.0, evidence/offset/descriptor refs. PR dữ liệu chưa chạy một lượt chấm live và không cung cấp số liệu độ chính xác mô hình.
