# Corpus đối chiếu đạo văn — UC-02

`corpus.jsonl` có **1.800 bài public**: 600 Academic Task 1 và 1.200 Task 2 dạng essay. Dùng văn bản để đối chiếu sao chép, không chứa điểm band hoặc nhãn chấm IELTS. Không yêu cầu trường `license`.

## Nguồn và cách chọn

| Nguồn public | Dòng đọc | Bị loại | Được chọn |
| --- | ---: | --- | ---: |
| [hai2131/IELTS-essays-task-1](https://huggingface.co/datasets/hai2131/IELTS-essays-task-1) | 13.925 | 5.075 bản trùng chuẩn hóa | 600 |
| [chillies/ielts-writing-task2-essays](https://huggingface.co/datasets/chillies/ielts-writing-task2-essays) | 8.049 | 4 bài dạng thư, 1 bài dưới 50 từ | 1.200 |

Task 1 phủ 7 dạng và 329 chuỗi đề; Task 2 phủ 25 chủ đề, mỗi chủ đề 48 bài. Publisher là hai tài khoản trong URL. Nguồn Task 2 mô tả thu thập từ Writing9; không tự xác thực danh tính người viết hoặc nguồn gốc người/AI của từng bài. Không dùng điểm/feedback nguồn làm nhãn gold.

Script giữ nguyên bài và lỗi gốc; khóa khử trùng dùng NFKC + casefold + gộp khoảng trắng. Mốc 50 từ là lựa chọn tiền xử lý cho đối chiếu, không phải ngưỡng 150/250 từ IELTS. Chọn luân phiên chủ đề/đề, thứ tự trong đề dựa trên hash; chặn bản trùng nguyên văn chuẩn hóa với 84 bài benchmark và 6 basic cases. Chưa loại hết near-duplicate/paraphrase.

## Sáu trường

`source_id`, `task_type`, `exam_question`, `text`, `topic`, `source_url`. `text` là văn bản được so khớp; đề/chủ đề chỉ là ngữ cảnh. URL viewer chỉ rõ dòng; commit và hash snapshot cố định nằm trong `manifest.json` để tái tạo chính xác.

## Dùng và tạo lại

Corpus đã đi kèm repository, người nhận không cần tải lại dataset để nạp tool. [Handoff Member 4](../../docs/member1_to_member4_handoff.md) ghi điều chỉnh loader cần thực hiện với schema này.

```powershell
python scripts/check_member1_data.py
python scripts/build_ielts_plagiarism_corpus.py --task1-limit 600 --task2-limit 1200
```

Lệnh tạo lại cần `pyarrow` trong requirements và mạng ở lần tải snapshot đầu; không cần API key. Cache Parquet ở `raw/` được ignore. Có cache thì thêm `--offline`. Script đọc hai file benchmark JSON và basic cases để loại giao nhau; không thay bài/nhãn/chia tập.

Thiếu/hỏng corpus phải báo lỗi thay vì trả kết luận không đạo văn. Member 4/5 dùng tập test đạo văn riêng để đo phát hiện ≥90% / gắn nhầm ≤10%; sự có mặt của corpus không phải bằng chứng đã đạt các chỉ tiêu này.
