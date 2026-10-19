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

Xem docs/member1_descriptor_contract.md để biết schema, lệnh chạy và cách Người 2 mở collection.
72 chunks riêng Task 1/Task 2, mỗi chunk là một ô criterion × band 1–9.
Band 0 được giữ riêng trong descriptor_provenance.json, không gán enum all_criteria hoặc task1_task2.
Provenance lưu SHA256 PDF và trang/bounding box từng ô. Chưa có người thứ hai kiểm tra chéo.
Không đưa corpus hoặc benchmark vào collection descriptors.

## Corpus plagiarism

data/corpus_plagiarism/manifest.json hiện chưa có tài liệu.
Định dạng bàn giao dự kiến theo Người 4: corpus.jsonl, mỗi dòng có source_id, text, source_url, license.
Chỉ thêm nguồn khi đã ghi tác giả và quyền sử dụng; nguồn không cho phân phối phải giữ ngoài repo.

## Benchmark và basic cases

evals/benchmark_dev/ và evals/benchmark_test/ hiện chưa có bài chấm chuẩn.
Benchmark cần tối thiểu 30 bài hai Task, band 4–8, bốn điểm tiêu chí cùng điểm tổng từ nguồn chấm hợp lệ.
Không dùng LLM gán điểm chuẩn. Điểm nguồn phải được giữ nguyên.
evals/data/5_basic_cases.json vẫn là placeholder; không tính là eval đã hoàn thành.

## Minh bạch AI

AI hỗ trợ xây parser theo tọa độ PDF, contract, validation, tests và script ChromaDB.
Test không thay kiểm tra nội dung độc lập hoặc đánh giá chất lượng chấm của Agent.
