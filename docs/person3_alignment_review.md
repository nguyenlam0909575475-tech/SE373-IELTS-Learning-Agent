> Cập nhật tích hợp 26/10/2026: chính sách hiện hành và cách nối thật ở [member4_handoff.md](member4_handoff.md) và [team_integration.md](team_integration.md). Các nhận định raw mean/adapter cũ dưới đây là lịch sử; code hiện gọi compute_band TV4 theo quy ước repository.

# Đối chiếu phân công mới — Lịch sử và quyết định đã chốt

Ngày18/10/2026. Phạm vi: nội dung tài liệu và code Người 3 đang có; không xác minh code của các thành viên khác.

## Tài liệu đã so sánh

- **Bản mới:** [Phan_Cong_Nhiem_Vu_Phase_1_2026-10-18.md](reference/Phan_Cong_Nhiem_Vu_Phase_1_2026-10-18.md),
  sao chép nguyên byte từ `C:/Users/Khanh/Downloads/Phan_Cong_Nhiem_Vu_Phase_1.md`.
- **Bản phân công cũ:** [Phan_Cong_Nhiem_Vu_Phase_1.md](reference/Phan_Cong_Nhiem_Vu_Phase_1.md).
- **Đề gốc của giảng viên:** [2026-10-06_de_tai_06_ielts_learning_agent.docx](reference/2026-10-06_de_tai_06_ielts_learning_agent.docx),
  đối chiếu trực tiếp văn bản và bảng trong DOCX, đặc biệt UC-02, mục2.2–2.3, 4.1–4.4, 6–7.
- **Code:** [schemas.py](../src/agent/schemas.py), [contracts.py](../src/agent/contracts.py),
  [nodes.py](../src/agent/nodes.py), [mock_services.py](../src/agent/mock_services.py), [tracing.py](../src/agent/tracing.py).

**Kết luận:** bản mới đã sửa đúng các lệch quan trọng về tên/schema so với đề gốc và khớp code
Người 3 ở các giao diện chính. Chưa thể coi toàn bộ yêu cầu đã được triển khai: còn khác policy
làm tròn theo đề xuất nhóm, cách gọi mã lỗi evidence, trace và các phần tích hợp/eval.
Các quyết định hiện hành ở mục 2; không thay code hoặc tài liệu nguồn.

## 1. Những gì thay đổi từ bản phân công cũ

| Hạng mục | Bản cũ → bản mới | Đối chiếu đề gốc / code hiện tại |
|---|---|---|
| Tên điểm | `task_band` → `overall_band` | Đúng UC-02; code đã khớp, không cần đổi tên |
| Tên tool | `compute_task_band` → `compute_band` | Đúng mục4.1; code đã khớp |
| Chi tiết schema | Bổ sung đủ `comment`, evidence, corrections và enums | Khớp bảng UC-02 và `schemas.py` |
| Cờ/lỗi | Làm rõ4 flags nghiệp vụ; validation errors tách riêng | Khớp đề gốc và core |
| Thứ tự tính toán | Số từ trước LLM; band tổng sau4 điểm; thêm plagiarism vào luồng | Khớp cách core hiện gọi dependency |
| Retry | Làm rõ2 lần sửa sau lần đầu, tổng3 calls | Khớp đề gốc và graph; lỗi hạ tầng dừng ngay |
| Metadata | “6 trường gốc” →5 trường gốc + `chunk_id` nội bộ | Đúng mục2.2; payload core vẫn6 metadata + `text`, không đổi shape |
| Band descriptor | Bỏ khẳng định Word bắt buộc số nguyên1–9 | Đúng: Word không ghi cứng range này; core hiện giới hạn số0–9 |
| Làm tròn | “Chuẩn IELTS” → quy ước nhóm, gần0.5 và hòa thì lên | Đề gốc không quy định công thức làm tròn một Task; MOCK core chưa làm tròn |
| Evidence offsets | Tìm được quote → kiểm cả vị trí, chỉ số0, end loại trừ | Khớp yêu cầu nguyên văn/vị trí; core khớp, cần N5 xử lý Unicode |
| Task1 off-topic | Ghi rõ trần Achievement≤5 là bổ sung của nhóm | Đúng cách phân biệt nguồn; core đang áp dụng cả hai Task |
| Benchmark | 10–15 bài, chia5/8–10 → tổng≥30 bài, hai Task, band4–8 | Khớp mục2.3; chưa có benchmark thật trong phần Người 3 |
| Eval | Bổ sung refs, MAE, ±0.5/±1, QWK, plagiarism/off-topic, token/cost/latency | Khớp mục6.2; 181 unit tests không thay các chỉ số này |
| Ngưỡng nghiệm thu | Nêu≥60% trong±0.5, ≥90% trong±1; plagiarism≥90%, gắn nhầm≤10% | Khớp UC-02 tiêu chí5–6; chưa có bằng chứng đạt |
| Regression | Bổ sung ít nhất2 phiên bản, ghi model/prompt/data version | Khớp mục6.3; chưa chạy eval regression thật |
| Trace | Bổ sung tham số/kết quả đã che, skill invocation, version, usage/cost | Khớp mục4.4 về quan sát; code hiện mới đáp ứng một phần |
| Repo/CI/secret | Thêm cấu trúc đích; bổ sung refs_validator, kiểm file tracked/lịch sử | Nhiều chi tiết là lựa chọn nhóm; core nằm đúng `src/agent`, chưa có toàn bộ repo đích |
| Phạm vi đồ án | Làm rõ UC chung Phase1 không thay UC mỗi SV, K1–K8, ≥1 tool ngoài, ≥2 skills | Phù hợp mục3, 4.1, 4.2; hiện chưa hoàn thành trong repo Người 3 |
| Deadline/slide | Gắn nhãn chưa xác minh27/10, 10+ cases; video≤15 phút theo Word | Đúng khi tách nguồn: video có trong mục7; các ảnh slide được viện dẫn chưa có ở workspace |

## 2. Quyết định hiện hành (đã đánh giá theo yêu cầu người dùng)

Quy ước cuối cùng nằm trong [bản tra cứu](handoff.md), mục 3–5. Đã chốt nội dung
tra cứu; đây là cập nhật tài liệu, không phải tuyên bố đã triển khai các module còn thiếu.

| ID | Quyết định | Tình trạng |
|---|---|---|
| D1 — Band | Trung bình bốn tiêu chí, giữ số chưa làm tròn ở cấp Task. Không áp quy tắc tổng bốn kỹ năng vào một bài. | Khớp `compute_band` hiện tại; khác đề xuất half-up của bản phân công mới. Nguồn/lý do trong bản tra cứu. |
| D2 — Evidence | Giữ `schema_invalid` khi Pydantic bắt thiếu/rỗng; `evidence_missing` cho lỗi validator N4. | Khớp core; cùng ngân sách repair, không đổi enum flags. |
| D3 — RAG | Dừng với `RETRIEVAL_INVALID` nếu không có descriptors hợp lệ; không tự bịa rubric. | Khớp core; N2 cần tuân thủ filters và manifest. |
| D4 — Interfaces | Giữ các Protocol/DTO đồng bộ trong `contracts.py`; dùng adapter cho module khác giao diện. | Dùng bản tra cứu để ghép N2/N4/N5. |
| D5 — Trace/cost | Chỉ metadata an toàn; giá trị chưa có là null, chưa giả định có skill invocation/cost thật. | Những trường còn thiếu bổ sung khi tích hợp; chưa ghi nhận hoàn thành trace theo mọi yêu cầu Word. |
| D6 — Trace mẫu | `traces/samples/` cho gói bàn giao; `artifacts/traces/` cho dữ liệu tạm. | Chưa tạo trace bàn giao production trong lần sửa tài liệu. |
| D7 — Input | Giữ `item_id/task_type/essay`, resolve bank có provenance; Task1 cần material. | Không cho client truyền đề tùy ý ngoài schema. |
| D8 — Nguồn | Dùng bản phân công mới làm tham chiếu phối hợp; bản tra cứu ghi rõ quyết định D1 khác half-up. | Giữ cả hai bản nguồn nguyên văn, không ghi đè để che khác biệt. |

## 3. Tích hợp với ZIP nhóm (24/10/2026)

Đã đọc ZIP code nhóm và tạo adapter N2/N4 tại ../src/agent/team_adapters.py. Skill N2 được chép vào ../skills/writing-assessment/; schema được sinh từ model Person 3. Graph nạp skill, gọi entrypoint checks và ghi skill_name/skill_version trong trace. Chi tiết và phần bị chặn bởi dữ liệu còn thiếu nằm trong team_integration.md.

Nhánh Person 3 vẫn có chế độ MOCK độc lập mặc định. Adapter production chưa chạy end-to-end trên các module đã hợp nhất: ZIP chưa có task bank, Chroma DB cần tái tạo local, và contract Band 0 chưa được nối. N4 validator còn rounding cũ; adapter giữ quyết định raw mean đã chốt và chuyển riêng view kiểm consistency.

LLM adapter có thật, nhưng thử nghiệm gần nhất gặp JSON400/429; không ghi nhận đã ổn định. Chưa có benchmark ≥30 bài và eval/regression để chứng minh độ chính xác band/plagiarism.

## 4. Chỗ bản mới còn diễn đạt chưa thật thống nhất

- Phần Người 3 mô tả trace đầy đủ hơn, nhưng bảng IV về log/trace vẫn là mô tả ngắn cũ và còn viện dẫn
  `Quydinh2.png`. Nên dẫn mục4.4 Word và ghi bảng là tóm tắt, tránh dùng làm checklist đầy đủ.
- Sơ đồ/phần Người 1 vẫn gọi “6 metadata chuẩn”; bảng IV giải thích chính xác hơn là5 metadata
  đề gốc + ID nội bộ. Đây là khác cách diễn đạt, không làm thay đổi payload6 metadata.
- “5 test cases cơ bản” có case độ dài tách3a/3b: nếu mỗi biến thể là một record thì thực tế có6
  records. Nên ghi5 nhóm/6 mẫu để N1 và N5 thống nhất cách đếm, không thay yêu cầu≥30 benchmark.
- Các khẳng định về slide Buổi01, quy mô nhóm2–4/5, hạn27/10 chưa được xác minh từ những nguồn
  đó trong phiên này; không xem câu ghi trong bản mới là bằng chứng giảng viên đã xác nhận.

**Đã chốt cách trao đổi và cách tính trong bản tra cứu.** Các thiếu hụt tích hợp/eval nêu trên vẫn
là việc triển khai tiếp theo; không suy ra đã đạt nghiệm thu IELTS từ việc cập nhật báo cáo.
