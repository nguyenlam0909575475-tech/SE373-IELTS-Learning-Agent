# Sửa bàn giao TV1 cho TV2: xác minh PDF và ổn định test Chroma

Ngày kiểm chứng: 20/10/2026. Phạm vi: Band Descriptors và pipeline TV1 → TV2.
Không bao gồm corpus plagiarism, benchmark Writing hoặc basic cases theo yêu cầu người dùng.

## 1. Mốc code và cách đưa thay đổi vào nhóm

- PR TV1: #5, nhánh `member1-IELTS-Band-Descriptors-Data&Script`, commit gốc `4b43f5386180b673f1a867744bd6963f708c6228`.
- PR TV2: #4, commit dùng để kiểm tương thích `149d5f47b1f1ff69f78e13ee006825787db0830b`.
- PR sửa lỗi mới nhắm vào nhánh TV1 để diff chỉ gồm hai sửa lỗi, regression test và báo cáo này.
- Không ghi đè nhánh TV1/TV2, không merge PR tự động. Xung đột PR #5 với main là việc tích hợp riêng.
- Sau khi nhận PR sửa lỗi, TV2 cần cập nhật nhánh từ TV1. File test Chroma dùng cùng nội dung đã có trong PR #4 nên không có hai cách sửa cạnh tranh; vẫn cần kiểm tra kết quả merge và chạy test trên commit hợp nhất.

## 2. Thay đổi sản phẩm trong PR này

### scripts/extract_descriptors.py

**Trước:** downloader kiểm SHA256, nhưng extractor chỉ kiểm chín trang, nhãn May 2023 và hình học bảng.
Đường tải PDF thủ công có thể bỏ qua downloader. PDF bị chỉnh nội dung nhưng giữ bố cục vẫn được trích xuất.

**Sau:**
- Dùng lại `EXPECTED_SHA256` từ downloader, không tạo một giá trị hash thứ hai.
- Đọc bytes PDF một lần, tính SHA256 và từ chối nguồn khác hash bằng `ValueError` trước khi parse.
- Mở chính bytes đã kiểm tra bằng PyMuPDF. Điều này tránh kiểm một bản file rồi đọc một bản khác nếu file trên đĩa đổi giữa hai thao tác.
- Dùng lại digest đã kiểm tra cho metadata/provenance.

**Lý do:** bảo đảm cả đường tải tự động và thủ công dùng cùng bản nguồn đã xác minh.
Ngay cả thay đổi metadata PDF cũng làm đổi hash và bị từ chối theo chính sách ghim nguồn.
Không tự cập nhật hash khi nhà phát hành thay PDF; phải kiểm lại nguồn/parser trước.

### tests/test_descriptor_data.py

Thêm `test_extraction_rejects_modified_pdf_with_same_layout`.
Test tạo PDF tạm từ nguồn thật, sửa metadata để giữ nguyên bố cục và nội dung bảng nhưng đổi hash,
rồi yêu cầu extractor báo lỗi SHA256.

Đã chạy trước sửa: test thất bại vì extractor không báo lỗi.
Đã chạy sau sửa: test đạt. Các test trích xuất nguồn hợp lệ và kiểm dữ liệu cũ vẫn giữ nguyên.

### tests/test_rebuild_vectorstore.py

Đưa đúng sửa fixture đã có trong PR TV2 về TV1:
- Thay vector giả giống nhau `[1, 0, 0]` cho mọi document bằng ba thành phần suy từ SHA256 của text.
- Vector ổn định theo đầu vào, không cần model hoặc mạng.
- Chroma persistence/query/filter vẫn chạy thật.
- Giữ nguyên assertion về 72 records, xóa stale ID, collection khác, số kết quả, bộ lọc và toàn bộ nội dung lưu trữ.
- Không sửa thuật toán embedding/rebuild trong sản phẩm và không giảm yêu cầu test.

**Lý do:** vector giả trùng nhau khiến truy vấn ANN sau upsert/xóa có thể trả thiếu kết quả.
Lần kiểm trước sửa đã tái hiện lỗi `2 != 3`; fixture này dành cho kiểm hợp đồng lưu trữ, không đo chất lượng ngữ nghĩa.

### docs/member1_handoff_fixes.md

Báo cáo hiện tại: nguyên nhân, sửa đổi, kiểm chứng, ảnh hưởng TV2 và giải thích các file review trước đó.

## 3. Giải thích “12 files edited” ở lượt review trước

Ở lượt review PR #4, công cụ tạo 12 file trong thư mục local `.review-pr4/`.
Đó là bản sao nội dung lấy từ commit PR #4 để chạy kiểm chứng, không phải 12 thay đổi sản phẩm mới,
không phải code do lượt review tự triển khai và chưa được commit/push từ thao tác đó.

| File được sao chép | Mục đích kiểm tra |
|---|---|
| src/tools/rag_descriptors.py | Lọc Task/criterion, kiểm metadata, lỗi, adapter TV3 và policy Band 0 |
| src/skill_checks.py | Chuyển tiếp validators TV4, không nuốt lỗi |
| evals/retrieval_eval.py | Công thức metric và hai chế độ query/criterion |
| evals/data/retrieval_queries.json | Phạm vi tám cặp Task/criterion và nhãn relevance sơ bộ |
| scripts/sync_writing_schema.py | Export/check schema từ model TV3 |
| skills/writing-assessment/checks.py | Điểm vào gọi checks |
| skills/writing-assessment/skill.yaml | Contract I/O, policy và trạng thái schema |
| tests/test_retrieval.py | Scope, lỗi, metadata và persistence Chroma |
| tests/test_retrieval_eval.py | Precision/Recall/MRR và mẫu số khi truy vấn lỗi |
| tests/test_skill_checks.py | Delegation, schema export và dependency failures |
| tests/test_rebuild_vectorstore.py | Fixture sửa sẵn của PR TV2 để chạy bộ test kết hợp |
| scripts/demo_retrieval.py | Cách demo và trace không chứa bài người học |

Ngoài ra, các file nền TV1/PDF/dữ liệu local được sao chép để chạy test.
Các ảnh trong `tmp/pdfs/`, DB tạm và PDF đã chỉnh để tái hiện lỗi đều là dữ liệu kiểm chứng local.
Thử đảo điều kiện kiểm Task/criterion hoặc kiểm band chỉ diễn ra tạm thời và đã khôi phục.
Không đưa thư mục review, PDF, toàn văn descriptors, DB binary hoặc môi trường Python vào PR mới.

## 4. Ảnh hưởng tới TV2

- Không đổi chữ ký `retrieve_descriptors(task_type, criterion, top_k=3)`.
- Không đổi 72 chunk IDs, sáu metadata, nội dung text hoặc cách biểu diễn hai policy Band 0.
- Không đổi collection `writing_descriptors`, embedding model hoặc DTO TV2.
- Không cần sửa retrieval, skill hay adapters TV2 chỉ để dùng hai sửa lỗi này.
- DB đã dựng từ PDF chuẩn không bắt buộc rebuild chỉ vì thay đổi kiểm hash; nguồn hợp lệ cho cùng dữ liệu.
- PDF khác hash bị dừng sớm thay vì âm thầm nạp. Đây là thay đổi hành vi có chủ đích.
- Fixture hash chỉ dùng trong test, không ảnh hưởng chất lượng ranking thật.
- Không tuyên bố cải thiện Precision/Recall/MRR hoặc hoàn tất tích hợp Agent TV3/validators TV4.

## 5. Kiểm chứng

Môi trường: Windows, Python 3.14, chromadb 1.5.9, PyMuPDF 1.28.2.

| Kiểm tra | Kết quả |
|---|---|
| Regression test PDF đổi hash trước sửa | Thất bại đúng kỳ vọng: không raise ValueError |
| Bộ test TV1 sau sửa | 9/9 đạt |
| Bộ test TV1 + TV2 với code sửa | 39/39 đạt |
| Test bị skip/loại bỏ | Không |
| Assertion nghiệp vụ test Chroma bị giảm | Không |

Lệnh chạy từ root checkout tương ứng:

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
```

Trong sandbox kiểm chứng, TEMP/TMP được trỏ vào thư mục tạm nằm trong workspace để tránh lỗi quyền ghi;
không thay đổi cấu hình ứng dụng để xử lý giới hạn sandbox.

Các kiểm tra thực tế đã thực hiện trước sửa trên cùng nguồn chuẩn:
PDF SHA256 khớp; 72 chunks và hai policy không có ký tự replacement;
dựng DB mới bằng embedding thật hai lần vẫn 72 records; toàn văn/metadata DB khớp dữ liệu trích xuất;
retriever TV2 trả ba chunks đúng phạm vi cho cả tám cặp Task/criterion và đọc được hai policy Band 0.
Sau sửa, test tái trích xuất nguồn chuẩn xác nhận output giữ nguyên; bộ 39 tests xác nhận tương thích.
Không coi các kiểm tra này là nghiệm thu chất lượng chấm Writing end-to-end.

## 6. Giới hạn và AI usage

Codex hỗ trợ phân tích nguyên nhân, thêm regression test, sửa extractor, tái sử dụng fixture TV2,
chạy kiểm chứng và viết báo cáo. Thành viên cần đọc hiểu trước khi merge/vấn đáp.
Không thêm dependency, không gọi LLM chấm bài và không dùng dữ liệu người học thật.
Chưa kiểm CI trên GitHub cho đến khi PR được tạo và workflow chạy; không khẳng định Actions đã xanh.
