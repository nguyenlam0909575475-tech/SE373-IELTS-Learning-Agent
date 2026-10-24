# Thiết kế và kiểm chứng RAG retrieval và skill Writing

Thành viên 2 triển khai công cụ tìm descriptors cho UC-02 và đóng gói quy trình
chấm thành skill tái sử dụng. Công cụ đã chạy trên ChromaDB và embedding thật;
chưa kiểm chứng kết quả chấm Writing của Agent vì chưa có core TV3, validators
TV4 và benchmark được ghép trong nhánh này. Hướng dẫn tích hợp ở
[member2_handoff.md](member2_handoff.md).

## Kiến trúc và quyền hạn

```text
PDF chính thức -> extractor TV1 -> 72 chunk (Task × criterion × band 1–9)
                                -> ChromaDB + ONNX embedding TV1
Agent TV3 -> retrieve_descriptors(task_type, criterion, top_k=3)
           -> AND filter test_part/criterion -> vector query
           -> kiểm tra metadata/ID/text -> DescriptorChunk hoặc RETRIEVAL_INVALID
Agent TV3 -> Pydantic -> skill checks -> ba validators TV4 -> repair/return
```

Chunk giữ nguyên bảy trường từ TV1. Mỗi lần truy xuất giới hạn 1–3 chunk;
Task 1 không dùng `task_response`, Task 2 không dùng `task_achievement`.
Sau khi Chroma lọc metadata, code vẫn kiểm lại Task, tiêu chí, ID duy nhất,
band nguyên 1–9, version, URL và text không rỗng/hỏng. Chỉ ID thực tế truy xuất
mới được làm refs cho validator. Không tạo rubric thay thế khi dữ liệu thiếu.

Đọc collection có sẵn bằng `get_collection`, không gọi create/upsert/delete.
Embedding là `DefaultEmbeddingFunction`, cùng ONNX all-MiniLM-L6-v2 với TV1.
Source/version khác phải được review; metadata nguồn không chứng minh toàn văn
đã được người thứ hai đối chiếu PDF. Các phép đo bên dưới cũng không thay kiểm
tra chéo nội dung trích xuất.

Band 0 là policy nguồn chung theo Task, được đọc riêng từ provenance có hash
PDF đã ghim, không nhân bản thành bốn chunk. Việc Agent áp dụng policy và xử lý
schema/refs tương ứng còn cần TV3 tích hợp. Bài ngắn và cờ plagiarism không tự
đồng nghĩa Band 0.

## Skill

Skill `writing-assessment` version `1.0.0` có mục đích, khi dùng, contract I/O,
quy trình, ràng buộc, ví dụ và final checks. `checks.py` chuyển tiếp validators
TV4 qua dependency injection, không chép lại logic và không thực thi lệnh shell.
Pydantic của TV3 là schema chuẩn; script sync sẽ xuất schema thật vào YAML và
JSON sau khi model có mặt. Hiện YAML ghi rõ chỉ là contract snapshot theo handoff.

Essay/task material/chunks được xử lý như dữ liệu, không phải lệnh hệ thống.
Tool đếm từ trước chấm; sau khi có bốn điểm, `compute_band` tính trung bình
và làm tròn đến nấc 0.5 gần nhất, đúng giữa hai mức thì lên (.25 lên .5,
.75 lên 1.0), theo file phân công Phase 1. Ví dụ `[6,6,6,7] -> 6.5`.
Đây là policy của nhóm cho một Task, không khẳng định là quy tắc IELTS chính
thức ở cấp Task. Quote dùng offset Python
Unicode, `end_char` loại trừ. Graph quản lý tối đa hai lượt sửa, không trả bản
chấm còn lỗi. Có nhãn AI ước lượng trên kết quả.

Việc có file skill không tự chứng minh runner đã nạp skill hoặc chống được
injection. TV3 phải tích hợp loading, invocation trace và chạy tập tấn công thực tế.

## Kiểm thử

Ngày 20/10/2026, Windows/Python 3.14, chromadb 1.5.9, PyMuPDF 1.28.2:
**38 unit/integration tests đạt**, gồm 8 tests sẵn có của TV1 và 30 tests mới.
Test Chroma dùng persistence và metadata filters thật, thay inference bằng
embedding deterministic để chạy offline; test này không đo chất lượng ngữ nghĩa.
Skill qua công cụ kiểm tra frontmatter/cấu trúc của Skill Creator.

Trong lần chạy lại, test persistence cũ của TV1 có lúc chỉ trả hai hàng khi mọi
chunk và record bị xoá đều dùng vector giả giống hệt nhau. Fixture đã đổi sang
vector giả ổn định theo hash text, giữ nguyên các assertion về count, filters,
stale IDs và collection khác. Không sửa thuật toán rebuild/retrieval để ép test
đạt; sau thay đổi toàn bộ 38 tests đạt.

Các bất biến được kiểm: đủ tám scope; không lẫn Task/criterion; không trả ID
trùng hoặc metadata sai; thiếu DB không tạo kho rỗng; lỗi không lộ nội dung backend;
policy Band 0 không có ref ID; adapter chuyển đúng factory/keyword; checks không
nuốt lỗi; metric khớp ví dụ tính tay; case truy xuất lỗi vẫn tính vào mẫu số.
Test DTO/validators dùng object giả theo handoff, chưa phải test graph TV3/TV4 thật.

## Kết quả retrieval thực tế

Đã tái tạo 72 chunks từ PDF có SHA256
`e3c88943ef92d98988ce4db454fd7fa8d8435f0b25e9ec667e3720a5c1168d1b`.
Chạy [retrieval_eval.py](../evals/retrieval_eval.py) với embedding ONNX thật,
16 truy vấn tự soạn, mỗi cặp Task/criterion có hai truy vấn hướng band 5 và 7.
Không lấy query nguyên văn từ ô được index. Mỗi query có một chunk relevant
được gán nhãn sơ bộ bằng hỗ trợ AI, chưa có review độc lập. Đây là đánh giá
ranking bổ sung, không phải benchmark có điểm chuẩn của bài Writing.

| Chế độ | Số query | Lỗi | Precision@3 | Recall@3 | MRR@3 |
|---|---:|---:|---:|---:|---:|
| `query`: mô tả đặc điểm bằng `retrieve_for_query` | 16 | 0 | 0.1875 | 0.5625 | 0.3854 |
| `criterion`: tool mặc định dùng câu truy vấn chung theo tiêu chí | 16 | 0 | 0.1458 | 0.4375 | 0.3333 |

Kết quả từng case, checksum tập query, version query và metadata index nằm tại
[member2_retrieval_results.json](member2_retrieval_results.json). Một query có
đúng một nhãn relevant nên Precision@3 tối đa là 1/3, không phải 1. Recall@3 ở
đây tương đương tỷ lệ case tìm được chunk đã gán nhãn trong top 3. MRR@3 là
nghịch đảo thứ hạng của hit đầu, bằng 0 nếu không có hit trong top 3; báo cáo
dùng trung bình macro. Query lỗi vẫn có metric 0, không bị loại khỏi mẫu số.

Lọc Task/criterion đúng không đồng nghĩa chọn đúng mức band. Ví dụ thực tế:

| Case chế độ query | Band mục tiêu theo nhãn | Ba band tìm được theo thứ tự |
|---|---:|---|
| task1_task_achievement_b5 | 5 | 2, 7, 6 |
| task1_coherence_cohesion_b5 | 5 | 8, 4, 7 |
| task1_lexical_resource_b7 | 7 | 5, 9, 4 |

Các lỗi có thể đến từ mô tả gần nghĩa giữa bands, query chưa đủ đặc trưng,
embedding tổng quát hoặc nhãn sơ bộ chưa chính xác; đây là giả thuyết, chưa
được xác nhận bằng review. Nên review nhãn với người khác trước, giữ tập này
cố định và tạo hold-out mới trước khi tune. Với chữ ký mặc định chỉ có Task và
criterion, hai bài khác nhau dùng cùng query nên không thể kỳ vọng retrieval
tự thích ứng trình độ từng bài. Entry point `retrieve_for_query` là lựa chọn để
TV3 ghép mô tả đặc điểm theo tiêu chí, nhưng việc đó chưa nằm trong graph thật.

Hai chế độ là hai cấu hình truy vấn trên cùng phiên bản, không phải hai lần
regression của hệ thống chấm theo Mục 6.3 đề tài. Chưa đo MAE, QWK, tỷ lệ quote
đúng, chống injection hay độ chính xác band; cần benchmark hợp lệ và Agent thật.

## Failure modes và cách xử lý

| Failure mode | Cơ chế hiện có | Phần còn cần |
|---|---|---|
| Thiếu DB/model hoặc lỗi query | RETRIEVAL_INVALID, dừng chấm | TV3 ánh xạ DependencyFailure thật |
| Backend trả nhầm Task/criterion | Bộ lọc cứng và hậu kiểm từng record | Chạy graph và refs validator TV4 thật |
| Không chọn được band cần tham khảo trong top 3 | Không bịa refs/rubric, skill yêu cầu dừng khi thiếu căn cứ | Review relevance, thử query thích ứng trên hold-out |
| Chunk có lệnh điều khiển | Skill yêu cầu giữ vùng dữ liệu và gọi security guard | Chạy guard/Agent thật, không coi metadata check là chống injection |
| Schema hoặc validators chưa merge | Dependency injection, sync script, ghi rõ trạng thái | Export schema thật và chạy integration/repair |

## Kịch bản demo khoảng ba phút

1. Mở `rag_descriptors.py`, chỉ bộ lọc `$and` và hậu kiểm. Giải thích khác nhau
   giữa `task_achievement` và `task_response` bằng tên trường, không cần chấm thử.
2. Chạy `.venv/Scripts/python.exe -B -m scripts.demo_retrieval`; tám lời gọi
   đúng scope. Mở trace chỉ có metadata; bản mẫu ở
   `traces/samples/member2_retrieval.json`, chưa phải trace UC-02 hoàn chỉnh.
3. Chạy test retrieval, minh hoạ case Task 2 chunk bị trả cho Task 1 sẽ bị từ chối.
4. Mở skill để trình bày tool count/compute, quote offsets, refs và giới hạn sửa;
   mở `checks.py` để chỉ ra nó gọi validators TV4 qua dependency injection.
5. Chạy `python -m evals.retrieval_eval`, giải thích bảng metric và giới hạn nhãn.
   Không tuyên bố hệ thống chấm Writing đã đạt các ngưỡng UC-02.

## Nguồn tham khảo

- [Chroma Python reference](https://docs.trychroma.com/reference/python) và
  [mã Collection của Chroma](https://github.com/chroma-core/chroma/blob/main/chromadb/api/models/Collection.py): API query/get collection và metadata filtering.
- [Band Descriptors chính thức](https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf): nguồn TV1 đã ghim; toàn văn chỉ để local khi chưa xác minh quyền phân phối.
- File phân công Phase 1 do nhóm cung cấp là căn cứ hợp đồng cho gói TV2.
  Hai handoff TV3/TV4 dùng tham khảo tích hợp; chỗ ghi không làm tròn cấp Task
  khác phân công và cần đồng bộ. Không tự xem handoff như code đã merge.
- [Minh bạch sử dụng AI](ai_usage.md).
