# SE373: IELTS Learning Agent (Đề tài 06)

> **Học phần:** Kỹ nghệ Hệ thống AI Tác tử (Agentic AI Systems Engineering — SE373)
> **Thời gian:** Học kỳ 1, Năm học 2026–2027
> **Đề tài:** Đề tài 06 — IELTS Learning Agent (Academic Training Companion)
> **Cơ sở quy định:** [`docs/Grading Criteria for the Final Project.md`](docs/Grading%20Criteria%20for%20the%20Final%20Project.md) & [`docs/Phan_Cong_Nhiem_Vu_Phase_1.md`](docs/Phan_Cong_Nhiem_Vu_Phase_1.md)

---

## 1. Giới thiệu tổng quan

**IELTS Learning Agent** là hệ thống AI đồng hành hỗ trợ người học tự luyện thi IELTS Academic toàn diện: kiểm tra đầu vào, chấm bài Writing/Speaking theo tiêu chí Band Descriptors công khai có dẫn chứng, sinh bài Reading/Listening luyện tập có kiểm chứng hai lớp, ghi nhớ điểm yếu dài hạn và lập kế hoạch học tập cá nhân hóa.

### Triết lý cốt lõi: Harness-First Architecture
> *"Giá trị của agent nằm ở **harness**, không nằm ở model."*

Thay vì phụ thuộc vào sinh văn bản tự do không kiểm soát của LLM, hệ thống xây dựng một tầng xác thực tất định (**Harness Layer**) đa lớp:
1. **Bảo mật & Cách ly dữ liệu:** Đóng gói văn bản bài làm trong thẻ phân cách `<student_essay>`, phát hiện và ngăn chặn triệt để kỹ thuật tấn công Prompt Injection (`injection_detected`).
2. **Không để LLM tính toán:** Số từ (`count_words`) và điểm làm tròn IELTS Official (nấc 0.5, quy tắc .25 lên .5, .75 lên 1.0) được tính toán 100% bằng code Python tất định (`compute_band`).
3. **Chống Hallucination tuyệt đối:** Mọi nhận xét chấm điểm bắt buộc phải trích dẫn nguyên văn (`verbatim quote`) kèm tọa độ ký tự chính xác `[start_char:end_char]` trong bài viết của thí sinh.
4. **Cơ chế Tự sửa sai (Self-Correction Retry):** Verification Node kiểm tra đầu ra; nếu sai lệch schema, quote không khớp hoặc mã descriptor sai task, Agent tự sửa lỗi tối đa 2 lần trước khi xuất bản kết quả.
5. **100% Live Agent Core:** Hệ thống vận hành trên nền tảng LangGraph StateGraph, tích hợp trực tiếp mô hình ngôn ngữ lớn (OpenAI / Gemini) kết hợp chặt chẽ với tầng Harness kiểm chứng phòng thủ chiều sâu (Defense-in-Depth).

---

## 2. Phân công nhiệm vụ & Độ phủ K1–K8

Hệ thống được thiết kế đáp ứng đầy đủ **8/8 Mảng kiến thức (K1–K8)** theo tiêu chuẩn đánh giá của môn học:

| Thành viên | Vai trò Phase 1 (UC-02) | Use Case sở hữu (Toàn đồ án) | Mảng kiến thức (K1–K8) |
| :--- | :--- | :--- | :---: |
| **👤 Người 1** | **Knowledge Base & Ingestion:** Thu thập 72 Band Descriptors chunks, script `rebuild_vectorstore.py`, 1.800 bài corpus đạo văn, tập benchmark Academic Writing 84 bài (dev/test) + 6 basic cases kèm ảnh Task 1. | **UC-02:** Writing Task 1/2 Grading Engine with Band Descriptors & Citations | **K1** (Model, Loop), **K3** (RAG) |
| **👤 Người 2** | **RAG Retrieval & Skill Package:** Xây dựng tool `retrieve_descriptors` (hard filter chống rò rỉ Task), đóng gói `skills/writing_assessment/`, đo Precision/Recall trên ChromaDB. | **UC-04:** Reading/Listening Practice Generator with 2-Layer Validator | **K2** (Tools, Skills), **K7** (Verification) |
| **👤 Người 3** | **Writing Examiner Agent Core:** Schema SSOT `WritingAssessment`, LangGraph Agent Loop, tích hợp live LLM (OpenAI/Gemini), cơ chế tự sửa sai Self-Correction retry (tối đa 2 lần). | **UC-07:** Dual-Examiner & Moderator Grading Committee | **K6** (Multi-Agent), **K7** (Verification) |
| **👤 Người 4** | **Deterministic Tools, Validators & CI/CD:** 3 tools (`count_words`, `compute_band`, `check_plagiarism`), bộ kiểm tra `quote_validator` (100% nguyên văn và tọa độ), GitHub Actions CI Pipeline. | **UC-08:** Grading Reliability, Stability & Adversarial Eval Suite | **K7** (Evaluation), **K8** (Security, Obs) |
| **👤 Người 5** | **Application, Automated Eval Runner & Integration:** FastAPI Backend, Web UI thi máy (Interactive Highlighting dẫn chứng, realtime counter, timer 40p), bộ chạy `evals/run.py` và tổng hợp Phase 1 Report. | **UC-05:** Study Plan with Memory & **UC-10:** Progress Report + Teacher HITL | **K4** (Memory), **K5** (HITL), **K8** (Audit) |

---

## 3. Cấu trúc thư mục dự án

```text
SE373-IELTS-Learning-Agent/
├── .github/workflows/
│   └── ci.yml                                    # GitHub Actions CI (Ruff lint + Pytest + Vectorstore check)
├── backend/                                      # [Người 5] FastAPI Backend Server
│   ├── config.py                                 # Cấu hình đường dẫn, regex đếm từ & API settings
│   ├── main.py                                   # REST API endpoints & static SPA server
│   └── live_service.py                           # Cầu nối tích hợp trực tiếp LangGraph Agent Core
├── frontend/                                     # [Người 5] Giao diện Web App thi máy (Computer-Delivered UI)
│   ├── index.html                                # Giao diện làm bài 2 Part, timer 40p, modal nộp bài & kết quả
│   ├── style.css                                 # Giao diện responsive, chuẩn thi máy & hiệu ứng quote glow
│   └── app.js                                    # Realtime counter, interactive highlight dẫn chứng
├── src/agent/                                    # [Người 3] LangGraph Agent Core Loop
│   ├── graph.py                                  # LangGraph StateGraph (resolve -> rubric -> examiner -> verify)
│   ├── gemini.py                                 # Gemini Live Examiner client
│   ├── openai_compatible.py                      # OpenAI / Groq Compatible Examiner client
│   ├── contracts.py                              # Data contracts nội bộ của Agent
│   ├── schemas.py                                # Pydantic Schemas SSOT
│   └── team_adapters.py                          # Adapter kết nối tools của Người 2, Người 4
├── skills/
│   └── writing_assessment/                       # [Người 2 & 3] Reusable Skill (UC-02)
│       ├── skill.yaml                            # Hợp đồng I/O Pydantic Schema
│       ├── instructions.md                       # Hướng dẫn quy trình chấm 4 tiêu chí
│       └── checks.py                             # Bộ kiểm tra Harness tất định (schema, offset, cap điểm, disclaimer)
├── agent/tools/                                  # [Người 2 & Người 4] Deterministic Tools
│   ├── compute_tool.py                           # count_words & compute_band tất định
│   ├── plagiarism_tool.py                        # check_plagiarism đối chiếu n-gram với corpus
│   └── rag_tool.py                               # retrieve_descriptors RAG tool truy xuất ChromaDB
├── data/
│   ├── bank/                                     # Ngân hàng đề thi có metadata source & license
│   ├── corpus_plagiarism/                        # [Người 1] 1.800 bài đối chiếu đạo văn (Task 1 & Task 2)
│   └── chroma_db/                                # Vectorstore sinh bởi script nạp barem (đã git-ignore)
├── evals/                                        # [Người 1, 4 & 5] Bộ đánh giá tự động
│   ├── benchmark_dev/benchmark.json              # 69 bài benchmark tập Dev (đầy đủ ground truth)
│   ├── benchmark_test/benchmark.json             # 15 bài benchmark tập Test
│   ├── data/5_basic_cases.json                   # 6 ca kiểm thử biên (under_length, off_topic, grammar)
│   ├── materials/                                # Ảnh đề bài Task 1 đi kèm benchmark
│   ├── run.py                                    # Script chạy eval tự động (xuất JSON & Markdown)
│   └── eval_report_phase1.md                     # Báo cáo đánh giá chi tiết Phase 1
├── scripts/
│   ├── rebuild_vectorstore.py                    # [Người 1] Script nạp 72 chunks Band Descriptors vào Chroma
│   ├── build_ielts_plagiarism_corpus.py          # [Người 1] Script đóng gói corpus đạo văn
│   ├── check_repository.py                       # [Người 4] Kiểm tra bí mật (secrets), PII và file cấm commit
│   └── check_writing_benchmark.py                # [Người 1] Script kiểm tra tính toàn vẹn benchmark
├── docs/                                         # Tài liệu kỹ thuật, bàn giao & phân công
│   ├── member1_handoff.md                        # Tài liệu tổng hợp bàn giao của Người 1
│   ├── member1_to_member2_handoff.md             # Bàn giao dữ liệu Descriptors cho RAG
│   ├── member1_to_member4_handoff.md             # Bàn giao Corpus đạo văn cho Công cụ tất định
│   ├── member1_to_member5_handoff.md             # Bàn giao Benchmark & Basic Cases cho App & Eval
│   ├── Phan_Cong_Nhiem_Vu_Phase_1.md             # Kế hoạch phân công Phase 1 chi tiết
│   ├── Grading Criteria for the Final Project.md # Tiêu chuẩn đánh giá đồ án môn học
│   └── data_sources.md                           # Nguồn gốc dữ liệu & chứng minh bản quyền
├── tests/                                        # Bộ kiểm thử tự động toàn diện (297/297 tests passed)
├── AGENTS.md                                     # Đặc tả kiến trúc Multi-Agent & quy định đóng băng giao diện
├── TEAM_NOTICE.md                                # Hướng dẫn phối hợp nhóm & phân quyền file
├── requirements.txt                              # Danh sách thư viện Python
├── pyproject.toml                                # Cấu hình môi trường pytest & ruff
└── .env.example                                  # Mẫu biến môi trường (an toàn, không chứa secret)
```

---

## 4. Hướng dẫn cài đặt & Khởi chạy

### Yêu cầu tiên quyết
* Python 3.10 trở lên (khuyến nghị Python 3.11 hoặc 3.12).
* Git.

### Bước 1: Khởi tạo môi trường ảo & Cài đặt thư viện
```bash
# 1. Clone repository
git clone https://github.com/nguyenlam0909575475-tech/SE373-IELTS-Learning-Agent.git
cd SE373-IELTS-Learning-Agent

# 2. Tạo và kích hoạt virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\Activate.ps1    # Windows PowerShell

# 3. Cài đặt các dependencies
pip install -r requirements.txt
```

### Bước 2: Cấu hình biến môi trường
Sao chép file mẫu `.env.example` thành `.env`:
```bash
cp .env.example .env
```
Mở file `.env` và điền API Key của mô hình ngôn ngữ bạn muốn sử dụng (hệ thống hỗ trợ OpenAI hoặc Gemini):
```env
# Lựa chọn 1: Cấu hình OpenAI (hoặc Groq / OpenAI-compatible endpoint)
OPENAI_API_KEY="your-openai-api-key-here"
OPENAI_BASE_URL="https://api.openai.com/v1"
OPENAI_MODEL="gpt-4o-mini"

# Hoặc Lựa chọn 2: Cấu hình Google Gemini
GEMINI_API_KEY="your-gemini-api-key-here"
GEMINI_MODEL="gemini-1.5-flash"
```

### Bước 3: Khởi tạo cơ sở dữ liệu Vector (ChromaDB)
Nạp 72 chunks tiêu chí Band Descriptors chính thức vào vectorstore:
```bash
python -B scripts/rebuild_vectorstore.py
```
> Khi chạy lần đầu, thư viện sẽ tự động tải mô hình embedding cục bộ `all-MiniLM-L6-v2` và lập chỉ mục trong `data/chroma_db/`.

### Bước 4: Khởi chạy Ứng dụng Web
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Mở trình duyệt truy cập: **`http://localhost:8000`** để trải nghiệm giao diện thi máy, bộ đếm từ realtime, làm bài Task 1/Task 2 và xem kết quả chấm có dẫn chứng tô màu tương tác.

### Bước 5: Chạy Bộ đánh giá tự động (Eval Runner)
Chạy đánh giá tự động trên bộ benchmark và các ca kiểm thử biên:
```bash
# Chạy bộ đánh giá (sử dụng Live LLM đã cấu hình trong .env):
python evals/run.py
```
Kết quả chi tiết sẽ được xuất ra console, lưu vào file [`eval_results.json`](eval_results.json) và tổng hợp tại [`evals/eval_report_phase1.md`](evals/eval_report_phase1.md).

### Bước 6: Chạy Bộ kiểm thử Unit Test & Linting
```bash
# Kiểm tra bí mật (secrets) và tuân thủ dữ liệu không rò rỉ:
python -B scripts/check_repository.py
python -B scripts/check_repository.py --history

# Kiểm tra cú pháp và định dạng với Ruff:
ruff check .

# Chạy toàn bộ 297 test cases:
pytest
```

---

## 5. Tài liệu bàn giao & Báo cáo kỹ thuật

* [Tổng hợp bàn giao Member 1](docs/member1_handoff.md)
* [Bàn giao Member 1 sang Member 2 (RAG Ingestion)](docs/member1_to_member2_handoff.md)
* [Bàn giao Member 1 sang Member 4 (Plagiarism Corpus)](docs/member1_to_member4_handoff.md)
* [Bàn giao Member 1 sang Member 5 (Benchmark & Basic Cases)](docs/member1_to_member5_handoff.md)
* [Kế hoạch triển khai & Loại bỏ Mock (Implementation)](Implementation.md)
* [Báo cáo đánh giá Phase 1 (Evaluation Report)](evals/eval_report_phase1.md)

---

## 6. Quy định bắt buộc của đề tài (Compliance Rules)

Mọi đóng góp vào repository phải tuân thủ nghiêm ngặt 4 quy tắc đề tài theo `Grading Criteria for the Final Project.md`:

1. **Không sao chép đề có bản quyền:** Tuyệt đối không dùng đề từ sách Cambridge IELTS hoặc tài liệu thương mại. Mọi đề thi trong `data/bank/` bắt buộc phải có 2 trường `source` và `license`.
2. **Nhãn ước lượng điểm do AI chấm (Rule 1.5.2):** Mọi kết quả hiển thị trên màn hình Web, API và file báo cáo bắt buộc phải kèm disclaimer:
   > *"Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức."*
3. **Bộ bài có điểm chuẩn hợp lệ:** Điểm chuẩn chỉ lấy từ bài mẫu công khai có band kèm nhận xét của giám khảo hoặc giáo viên chấm; không dùng LLM để gán điểm chuẩn.
4. **Bảo vệ dữ liệu người học:** Chỉ sử dụng hồ sơ người học giả lập. Tuyệt đối không commit bài làm thật, âm thanh, thông tin cá nhân của người dùng vào repo.


## Ghi chú tích hợp TV4 (27/10/2026)

- Corpus mặc định là bộ 1.800 bài TV1; loader không bắt buộc license và không sửa nội dung corpus.
- Giữ giao diện thi mới TV5. Web sử dụng live agent; `USE_MOCK_AGENT=true` không bật mock trên web.
- Task 1 text-only cần số liệu/chú giải thật qua `task_material_text`. Có ô nhập dữ liệu này ở phần đề bài.
- ChromaDB cần được dựng theo hướng dẫn bên trên; kiểm thử unit không tự tải embedding hoặc tạo DB.
- CLI `evals/run.py --mock` dùng bộ giả lập offline riêng để kiểm tra luồng, không gọi LLM.
- Có thể thêm `--benchmark-test evals/benchmark_test/benchmark.json` để báo cáo dev/test riêng;
  báo cáo gồm MAE bốn tiêu chí và các điều kiện basic cases.
- Bản ghép PR #19 với TV4: 315 test Python khả dụng và 3 test renderer Node pass.
  Test PDF/Chroma chưa chạy đầy đủ do thiếu dependency; chưa xác nhận chất lượng inference live.
- Chi tiết giao tiếp corpus, schema và lỗi: [bàn giao TV4](docs/member4_handoff.md).
