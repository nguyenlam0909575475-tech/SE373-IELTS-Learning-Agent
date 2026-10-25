# Nguồn dữ liệu Người 1

## Band Descriptors

- Nguồn chính thức: https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf
- Tác giả/chủ thể công bố: các tổ chức đồng sở hữu IELTS; tài liệu công bố trên IELTS.org.
- Phiên bản: Updated May 2023; bản ghi tải ban đầu: 2026-10-18 trong data/raw/descriptors/download_info.json.
- PDF đã có tại thư mục gốc. Extractor không tự tải hoặc tự xác nhận ngày tải.
- Quyền phân phối lại: CHƯA XÁC MINH. Publicly accessible không phải giấy phép mở.
- PDF, JSON trích xuất và provenance để local và được ignore; nếu đã tracked, ignore không tự gỡ khỏi Git.
- Không sử dụng đề Cambridge, sách thương mại hoặc tài liệu không được phép để làm ngân hàng đề.

## Cấu trúc và tái tạo

Xem docs/member1_to_member2_handoff.md để biết schema, lệnh chạy và cách Người 2 mở collection.
72 chunks riêng Task 1/Task 2, mỗi chunk là một ô criterion × band 1–9.
Band 0 được giữ riêng trong descriptor_provenance.json, không gán enum all_criteria hoặc task1_task2.
Provenance lưu SHA256 PDF và trang/bounding box từng ô. Chưa có người thứ hai kiểm tra chéo.
Không đưa corpus hoặc benchmark vào collection descriptors.

## Corpus plagiarism

data/corpus_plagiarism/manifest.json hiện chưa có tài liệu.
Định dạng bàn giao dự kiến theo Người 4: corpus.jsonl, mỗi dòng có source_id, text, source_url, license.
Chỉ thêm nguồn khi đã ghi tác giả và quyền sử dụng; nguồn không cho phân phối phải giữ ngoài repo.

## Benchmark và basic cases (Cập nhật theo hướng dẫn mới của Giảng viên)

- **Tập Benchmark 30 bài (`evals/writing_benchmark_30.json`):**
  - Nguồn dữ liệu mở: Tuyển chọn từ hai dataset mở uy tín trên Hugging Face:
    + Task 2: `chillies/IELTS-writing-task-2-evaluation` (Hugging Face).
    + Task 1: `hai2131/IELTS-essays-task-1` (Hugging Face).
  - Quy mô: 30 bài viết (12 bài Task 1 và 18 bài Task 2) với dải Band từ 5.0 đến 7.5, bao phủ đa dạng dạng bài (Line graph, Bar chart, Pie chart, Table, Climograph, Opinion, Discussion, Problem-Solution).
  - Phương pháp xây dựng nhãn: Thực hiện quy trình rà soát thủ công (Human-in-the-loop review) bởi các thành viên nhóm SE373 Team 06. Toàn bộ điểm 4 tiêu chí (`task`, `coherence`, `lexical`, `grammar`) và điểm tổng `ground_truth_band` đã được đối chiếu trực tiếp với Band Descriptors chính thức, loại bỏ hoàn toàn các đoạn văn nối trùng lặp.
  - Nhãn phân loại: Đánh dấu `label_status: "human_verified"`, `reviewed_by: "SE373_Team_06"`.

- **Tập ca kiểm thử chức năng biên (`evals/data/5_basic_cases.json`):**
  - Gồm 6 ca kiểm thử biên chức năng (Functional Boundary Test Cases): bài Task 1 & Task 2 chuẩn, hai ca kiểm tra thiếu độ dài (<150 từ và <250 từ cho cờ `under_length`), ca lạc đề hoàn toàn (cờ `off_topic` kèm cap $\le 5.0$), và ca lỗi ngữ pháp cơ bản (cờ `corrections`).
  - Đã được nhóm rà soát và gắn nhãn xác nhận `label_status: "human_verified"`.

## Minh bạch AI

AI hỗ trợ xây parser theo tọa độ PDF, contract, validation, tests và script ChromaDB.
Test không thay kiểm tra nội dung độc lập hoặc đánh giá chất lượng chấm của Agent.
