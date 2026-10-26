# Benchmark IELTS Academic Writing — UC-02

Bộ dữ liệu gồm **84 bài**, có đề, bài làm, bốn điểm tiêu chí, điểm tổng và nhận xét từ nguồn công khai. Bộ này dùng để đánh giá chấm điểm Writing; tách biệt với corpus đối chiếu đạo văn và basic cases kiểm tra hành vi.

| Tập | Task 1 | Task 2 | Tổng | Sử dụng |
| --- | ---: | ---: | ---: | --- |
| [benchmark_dev/benchmark.json](benchmark_dev/benchmark.json) | 21 | 48 | 69 | Phát triển và điều chỉnh prompt |
| [benchmark_test/benchmark.json](benchmark_test/benchmark.json) | 10 | 5 | 15 | Hold-out, đánh giá sau khi khóa cấu hình |
| Tổng | 31 | 53 | 84 | Band tổng từ 4.0 đến 8.0 |

Task 1 chỉ gồm Academic report, không có thư General Training. Task 2 là bài luận phù hợp Academic.

## Nguồn dữ liệu

| Nguồn | Số bài | Dữ liệu sử dụng |
| --- | ---: | --- |
| [IELTS Juice](https://ieltsjuice.com/) | 22 | Bài gốc, đề, hình Task 1, điểm và feedback |
| [IELTS Online Tests](https://ieltsonlinetests.com/) | 15 | Bài gốc trên trang writing correction, điểm và feedback |
| [IELTS-Blog](https://www.ielts-blog.com/) | 17 | Bài luận, điểm công bố và nhận xét |
| [Mc IELTS](https://mcielts.com/) | 25 | Bài gốc, đề/hình, bảng điểm và nhận xét trên trang/ảnh |
| [IELTS Answers](https://www.ieltsanswers.com/) | 4 | Bài gốc trong PDF, bảng điểm và nhận xét |
| [Belajar IELTS](https://belajar-ielts.blogspot.com/2024/06/task-2-agree-disagree-band-50-to-65.html) | 1 | Bài shopping gốc band 5.0; không dùng bản sửa 6.5 |

URL chính xác của từng bài nằm trong trường `source`. Một URL có thể chứa nhiều bài; mỗi bài vẫn có `case_id` riêng.

## Phương pháp xây dựng nhãn

1. Lấy bài viết gốc và đề tương ứng từ nguồn công khai; giữ lỗi chính tả, ngữ pháp và cách chia đoạn của bài gốc. Với bài có sửa trực tiếp, tách phần chỉnh sửa khỏi bài để tránh chấm nhầm bản đã sửa.
2. Trích **bốn điểm tiêu chí và điểm tổng do nguồn công bố**, cùng nhận xét. Nhận xét chung được chấp nhận, không bắt buộc nhận xét riêng từng tiêu chí. Với dữ liệu nằm trong ảnh/PDF, chép nội dung và điểm theo đúng phiên bản bài gốc.
3. Chuẩn hóa tên tiêu chí: Task 1 dùng `task_achievement`, Task 2 dùng `task_response`; ba tiêu chí còn lại là `coherence_cohesion`, `lexical_resource`, `grammatical_range_accuracy`. Nếu nguồn gọi tiêu chí đầu bằng tên khác, ánh xạ theo Task; không đổi giá trị điểm.
4. Giữ nguyên điểm tổng của nguồn, không thay bằng trung bình tự tính. Không dùng LLM để tự tạo điểm chuẩn mới cho bộ dữ liệu này.
5. Dùng bản phân chia dev/test đã cố định; không đưa cùng bài, đề trùng nguyên văn hoặc cùng hình Task 1 vào hai tập.

Nhãn là điểm đánh giá được nguồn công bố, không mặc nhiên là kết quả thi IELTS chính thức được xác thực. Không đưa các đề này vào ngân hàng đề của sản phẩm.

## Cấu trúc một bài

Hai file JSON đều là mảng. Mỗi bài có **8 trường**:

| Trường | Nội dung |
| --- | --- |
| `case_id` | Mã bài duy nhất |
| `task_type` | `task1` hoặc `task2` |
| `exam_question` | Đề bài |
| `essay` | Bài làm gốc |
| `material` | Đường dẫn ảnh Task 1 tính từ gốc repository; Task 2 là `null` |
| `scores` | Bốn điểm tiêu chí và `overall_band` |
| `feedback` | Nhận xét trích từ nguồn |
| `source` | URL nguồn của bài |

Không lưu `split` vì đã phân biệt bằng thư mục; không lưu `word_count` vì có thể tính từ `essay`.

Ví dụ cấu trúc `scores` cho Task 1:

```json
{
  "task_achievement": 6.0,
  "coherence_cohesion": 6.0,
  "lexical_resource": 6.0,
  "grammatical_range_accuracy": 5.0,
  "overall_band": 6.0
}
```

Task 2 thay `task_achievement` bằng `task_response`. Ví dụ trên chỉ minh họa cấu trúc, không phải nhãn mới.

## Hướng dẫn cho người nhận bàn giao

1. Clone repository và chạy kiểm tra từ thư mục gốc; script chỉ cần Python, không cần API key:

   ```powershell
   python scripts/check_writing_benchmark.py
   ```

2. Đọc dữ liệu và nạp ảnh theo đường dẫn trong repository:

   ```python
   import json
   from pathlib import Path

   root = Path.cwd()  # Chạy từ thư mục gốc repository
   rows = json.loads((root / "evals/benchmark_dev/benchmark.json").read_text(encoding="utf-8"))
   row = rows[0]
   image_bytes = (root / row["material"]).read_bytes() if row["material"] else None
   ```

3. Đăng ký đề từ `exam_question` và ảnh từ `material` vào TaskBank adapter của runner, lấy `case_id` làm `item_id`. Submission gửi Agent chỉ gồm:

   ```python
   submission = {
       "item_id": row["case_id"],
       "task_type": row["task_type"],
       "essay": row["essay"]
   }
   ```

4. Task 1 phải cung cấp nội dung ảnh cho mô hình qua adapter; chuỗi đường dẫn trong JSON tự nó không thay thế ảnh. Nếu API nhận ảnh dạng base64, mã hóa `image_bytes` và gửi kèm MIME tương ứng. **Không gửi `scores`, `feedback` hoặc trang nguồn có đáp án vào prompt chấm.**
5. Điều chỉnh prompt trên dev, sau đó khóa cấu hình trước khi chạy test. So sánh dự đoán với `scores`, báo cáo MAE theo từng tiêu chí và overall; báo cáo dev và hold-out riêng. Khi nghiệm thu toàn bộ UC-02, chạy đủ 84 bài và ghi rõ đây là kết quả toàn bộ benchmark.

## Xem ảnh Task 1 trên GitHub

Các ảnh nằm trong [materials/](materials/). Có **26 ảnh cho 31 bài Task 1** vì một số bài dùng chung đề. Mở [trang xem ảnh](materials/README.md) để thấy ảnh và các `case_id` sử dụng ảnh. Thư mục cũng có một biểu đồ riêng cho basic cases.

`material` lưu dạng `evals/materials/ten_anh.png`, không dùng `localhost` hoặc đường dẫn ổ C. Markdown dùng link ảnh tương đối; GitHub hiển thị ảnh theo đúng repository/branch, còn người clone dùng được file đi kèm. Cách dùng đường dẫn này được mô tả trong [GitHub Docs](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#relative-links).

Khi đưa lên GitHub, thêm **cả JSON và ảnh**, không chỉ thêm tài liệu. Chạy tại checkout Git của nhóm, kiểm tra các thay đổi được stage trước khi commit:

```powershell
git status
git add -A -- evals scripts docs tests .gitignore data/corpus_plagiarism/manifest.json data/corpus_plagiarism/README.md
git diff --cached --stat
git commit -m "Simplify Writing benchmark handoff and include Task 1 images"
git push
```

Các file JSON benchmark và `evals/materials/` không bị ignore. Thư mục `data/benchmark_local/` chỉ là cache làm việc, không cần gửi cho người nhận. Nếu gọi API bắt buộc dùng URL ảnh, dùng URL Raw của ảnh **sau khi ảnh đã được push**; repository private cần cơ chế truy cập phù hợp, hoặc nạp bytes từ bản clone như ví dụ trên.

Basic cases nằm ở [data/5_basic_cases.json](data/5_basic_cases.json), có [hướng dẫn riêng](../docs/member1_to_member5_handoff.md); không dùng `scores=null` của bộ này để tính sai số band.
