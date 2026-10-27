# Nguồn dữ liệu

## IELTS Writing Band Descriptors

- Nguồn: [IELTS.org — Writing Band Descriptors](https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf).
- Đơn vị công bố: các tổ chức đồng sở hữu IELTS; phiên bản Updated May 2023.
- Trích theo ô tiêu chí × band, tách Task 1 và Task 2; giữ nguyên các cấp band của nguồn.
- Hướng dẫn tạo ChromaDB và bàn giao retrieval: [member1_to_member2_handoff.md](member1_to_member2_handoff.md).

## Benchmark Academic Writing

Bộ dữ liệu gồm **84 bài: 31 Task 1 và 53 Task 2**, chia **69 dev / 15 test**, band tổng 4.0–8.0. Mỗi bài có đủ bốn điểm tiêu chí, điểm tổng, nhận xét và URL nguồn. Task 1 đi kèm ảnh đề trong repository.

Nguồn gồm IELTS Juice, IELTS Online Tests, IELTS-Blog, Mc IELTS, IELTS Answers và Belajar IELTS. Nhãn được trích từ **điểm do nguồn công bố**; giữ bài gốc và lỗi gốc, ánh xạ tên tiêu chí theo Task, không tự tạo band bằng LLM hoặc thay điểm tổng bằng trung bình tự tính.

Danh sách nguồn, schema tám trường và hướng dẫn dùng/dev/test/GitHub: [evals/README.md](../evals/README.md). URL chính xác của từng bài ở trường `source` trong file dữ liệu. Những đề này chỉ dùng cho đánh giá, không đưa vào ngân hàng đề sản phẩm.

## Corpus đối chiếu đạo văn

**1.800 bài**, gồm 600 Task 1 từ [hai2131/IELTS-essays-task-1](https://huggingface.co/datasets/hai2131/IELTS-essays-task-1) và 1.200 Task 2 từ [chillies/ielts-writing-task2-essays](https://huggingface.co/datasets/chillies/ielts-writing-task2-essays). Publisher lần lượt là hai tài khoản `hai2131` và `chillies`; nguồn Task 2 mô tả thu thập từ Writing9.

Dùng nguồn public, giữ nguyên văn bản, loại thư và bản trùng chuẩn hóa, chọn đa dạng chủ đề; không lấy điểm nguồn làm nhãn. Corpus không trộn với benchmark hoặc descriptors. Chi tiết nguồn và cách tạo lại: [corpus README](../data/corpus_plagiarism/README.md).

## Basic cases

[5_basic_cases.json](../evals/data/5_basic_cases.json) gồm 5 nhóm/6 bài kiểm tra hành vi, `scores=null`. Bài viết và đề lấy từ IELTS.org; câu hỏi sức khỏe đối chiếu IDP; biểu đồ phương tiện đến trường có đủ chú giải lấy từ Engnovate. Task 1 dùng cả `exam_question` và ảnh trong `material`. Case lạc đề dùng bài và đề được cung cấp cho tình huống kiểm thử. Nguồn cụ thể và hướng dẫn chạy ở [member1_to_member5_handoff.md](member1_to_member5_handoff.md).
