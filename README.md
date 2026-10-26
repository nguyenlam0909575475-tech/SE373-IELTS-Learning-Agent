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
1. **Bảo mật & Cách ly dữ liệu:** Đóng gói văn bản bài làm trong thẻ phân cách `<student_essay>`, ngăn chặn triệt để kỹ thuật tấn công Prompt Injection (`injection_detected`).
2. **Không để LLM tính toán:** Số từ (`count_words`) và điểm làm tròn IELTS Official (nấc 0.5, quy tắc .25 lên .5, .75 lên 1.0) được tính toán 100% bằng code Python tất định (`compute_band`).
3. **Chống Hallucination tuyệt đối:** Mọi nhận xét chấm điểm bắt buộc phải trích dẫn nguyên văn (`verbatim quote`) kèm tọa độ ký tự chính xác `[start_char:end_char]` trong bài viết của thí sinh.
4. **Cơ chế Tự sửa sai (Self-Correction Retry):** Verification Node kiểm tra đầu ra; nếu sai lệch schema, quote không khớp hoặc mã descriptor sai task, Agent tự sửa lỗi tối đa 2 lần trước khi xuất bản.
5. **Công tắc Mock / Live Agent:** Hỗ trợ biến cờ `USE_MOCK_AGENT` cho phép chuyển đổi mượt mà giữa chế độ giả lập offline đạt chuẩn Harness và chế độ gọi Agent LLM thực tế.

---

## 2. Phân công nhiệm vụ & Độ phủ K1–K8

Hệ thống được thiết kế đáp ứng đầy đủ **8/8 Mảng kiến thức (K1–K8)** theo tiêu chuẩn đánh giá của môn học:

| Thành viên | Vai trò ngang Phase 1 (UC-02) | Use Case sở hữu (Toàn đồ án) | Mảng kiến thức (K1–K8) |
| :--- | :--- | :--- | :---: |
| **👤 Người 1** | **Knowledge Base & Ingestion:** Thu thập Band Descriptors (đủ 6 metadata), script `rebuild_vectorstore.py`, tập benchmark Writing 30 bài + 5 test cases cơ bản. | **UC-02:** Writing Task 1/2 Grading Engine with Band Descriptors & Citations | **K1** (Model, Loop), **K3** (RAG) |
| **👤 Người 2** | **RAG Retrieval & Skill Package:** Xây dựng tool `retrieve_descriptors` (hard filter chống rò rỉ Task), đóng gói `skills/writing-assessment/`, đo Precision/Recall. | **UC-04:** Reading/Listening Practice Generator with 2-Layer Validator | **K2** (Tools, Skills), **K7** (Verification) |
| **👤 Người 3** | **Writing Examiner Agent Core:** Schema SSOT `WritingAssessment`, LangGraph Agent Loop, luồng tự sửa sai Self-Correction retry (tối đa 2 lần). | **UC-07:** Dual-Examiner & Moderator Grading Committee | **K6** (Multi-Agent), **K7** (Verification) |
| **👤 Người 4** | **Deterministic Tools, Validators & CI/CD:** 3 tools (`count_words`, `compute_band`, `check_plagiarism`), bộ kiểm tra `quote_validator` (100% nguyên văn và tọa độ), GitHub Actions CI. | **UC-08:** Grading Reliability, Stability & Adversarial Eval Suite | **K7** (Evaluation), **K8** (Security, Obs) |
| **👤 Người 5** | **Application, Automated Eval Runner & Demo:** FastAPI Backend, Web UI (Interactive Highlighting dẫn chứng, realtime counter, timer 40p), bộ chạy `evals/run.py` và video demo. | **UC-05:** Study Plan with Memory & **UC-10:** Progress Report + Teacher HITL | **K4** (Memory), **K5** (HITL), **K8** (Audit) |

---

## 3. Cấu trúc thư mục dự án

```text
SE373-IELTS-Learning-Agent/
├── .github/workflows/
│   └── ci.yml                                    # GitHub Actions CI (Ruff lint + Pytest)
├── backend/                                      # [Người 5] FastAPI Backend Server
│   ├── config.py                                 # Cấu hình biến công tắc USE_MOCK_AGENT & Regex
│   ├── main.py                                   # REST API endpoints & static SPA server
│   ├── mock_service.py                           # Giả lập đánh giá đạt 100% chuẩn Harness
│   └── live_service.py                           # Cầu nối tích hợp Agent Loop LLM thực tế
├── frontend/                                     # [Người 5] Giao diện Web App tương tác
│   ├── index.html                                # Giao diện làm bài, timer 40p, kết quả & disclaimer
│   ├── style.css                                 # Giao diện responsive & hiệu ứng neon quote glow
│   └── app.js                                    # Realtime counter, interactive highlight dẫn chứng
├── agent/
│   ├── core/                                     # [Người 3] LangGraph Loop & Committee
│   │   ├── state.py                              # Runtime AgentState
│   │   ├── loop.py                               # LangGraph StateGraph Loop
│   │   └── committee.py                          # Dual-Examiner & Moderator workflow (UC-07)
│   └── tools/                                    # [Người 2 & Người 4] Deterministic Tools
│       ├── compute_tool.py                       # count_words & compute_band
│       ├── plagiarism_tool.py                    # check_plagiarism against corpus
│       └── rag_tool.py                           # retrieve_descriptors RAG tool
├── skills/
│   └── writing_assessment/                       # [Người 2 & 3] Reusable Skill (UC-02)
│       ├── skill.yaml                            # Hợp đồng I/O Pydantic Schema
│       ├── instructions.md                       # Hướng dẫn quy trình chấm 4 tiêu chí
│       └── checks.py                             # Bộ kiểm tra Harness tất định (schema, offset, disclaimer)
├── data/
│   ├── bank/                                     # [Người 1] Ngân hàng đề có license & source
│   ├── corpus_plagiarism/                        # [Người 1] Tập văn bản đối chiếu đạo văn
│   └── chroma_db/                                # Vectorstore sinh bởi script (đã git-ignore)
├── evals/                                        # [Người 1, 4 & 5] Bộ đánh giá tự động
│   ├── writing_benchmark_30.json                 # 30 bài benchmark có ground truth
│   ├── adversarial_attacks.json                  # 5 bài tấn công biên (injection, plagiarism, off-topic)
│   ├── run.py                                    # Script chạy eval tự động (xuất JSON & Markdown)
│   └── eval_report_phase1.md                     # Báo cáo đánh giá chi tiết Phase 1
├── scripts/
│   └── rebuild_vectorstore.py                    # [Người 1] Script nạp Band Descriptors vào Chroma
├── docs/                                         # Tài liệu đặc tả kỹ thuật & phân công
│   ├── Phan_Cong_Nhiem_Vu_Phase_1.md             # Kế hoạch phân công Phase 1 đã chốt
│   ├── Grading Criteria for the Final Project.md # Tiêu chuẩn đánh giá đồ án môn học
│   └── data_sources.md                           # Nguồn gốc dữ liệu & chứng minh bản quyền
├── tests/                                        # Bộ kiểm thử tự động (18/18 tests passed)
├── AGENTS.md                                     # Đặc tả kiến trúc Multi-Agent & Harness Layer
├── TEAM_NOTICE.md                                # Hướng dẫn phối hợp nhóm & phân quyền file
├── requirements.txt                              # Danh sách thư viện Python
├── pyproject.toml                                # Cấu hình môi trường pytest & ruff
└── .env.example                                  # Mẫu biến môi trường (an toàn, không chứa secret)
```

---

## 4. Hướng dẫn cài đặt & Khởi chạy

### Yêu cầu tiên quyết
* Python 3.10 trở lên.
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
Mặc định hệ thống bật `USE_MOCK_AGENT="true"` giúp khởi chạy ngay lập tức mà không cần API key.

### Bước 3: Khởi chạy Ứng dụng Web
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Mở trình duyệt truy cập: **`http://localhost:8000`** để trải nghiệm giao diện làm bài, đếm từ realtime và tô sáng dẫn chứng tương tác.

### Bước 4: Chạy Bộ đánh giá tự động (Eval Runner)
```bash
# Chạy đánh giá toàn diện trên 30 bài benchmark + 5 bài tấn công biên:
python evals/run.py --mock
```
Kết quả sẽ xuất ra console, lưu file [`eval_results.json`](eval_results.json) và cập nhật [`evals/eval_report_phase1.md`](evals/eval_report_phase1.md).

### Bước 5: Chạy Kiểm thử Unit Test & Linting
```bash
# Chạy toàn bộ 18 test cases
pytest

# Kiểm tra cú pháp với Ruff
ruff check .
```

---

## 5. Quy định bắt buộc của đề tài (Compliance Rules)

Mọi đóng góp vào repository phải tuân thủ nghiêm ngặt 4 quy tắc đề tài theo `Grading Criteria for the Final Project.md`:

1. **Không sao chép đề có bản quyền:** Tuyệt đối không dùng đề từ sách Cambridge IELTS hoặc tài liệu thương mại. Mọi đề thi trong `data/bank/` bắt buộc phải có 2 trường `source` và `license`.
2. **Nhãn ước lượng điểm do AI chấm (Rule 1.5.2):** Mọi kết quả hiển thị trên màn hình Web, API và file báo cáo bắt buộc phải kèm disclaimer:
   > *"Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức."*
3. **Bộ bài có điểm chuẩn hợp lệ:** Điểm chuẩn chỉ lấy từ bài mẫu công khai có band kèm nhận xét của giám khảo hoặc giáo viên chấm; không dùng LLM để gán điểm chuẩn.
4. **Bảo vệ dữ liệu người học:** Chỉ sử dụng hồ sơ người học giả lập. Tuyệt đối không commit bài làm thật, âm thanh, thông tin cá nhân của người dùng vào repo.
# SE373-IELTS-Learning-Agent
Kho lưu trữ để build website Agentic AI hoàn chỉnh

## Member 1 handoff

See [Member 1 to Member 2 handoff](docs/member1_to_member2_handoff.md) for installation, data generation and retrieval integration.

## Member 2 retrieval and skill

See [Member 2 handoff](docs/member2_handoff.md) for the retrieval tool, Writing
skill, test/evaluation commands and the remaining Member 3/4 integration steps.
See [RAG and skill report](docs/member2_rag_skill_report.md) for design and demo.

After rebuilding the Member 1 index, run from the repository root:

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
.venv/Scripts/python.exe -B -m evals.retrieval_eval
.venv/Scripts/python.exe -B -m scripts.demo_retrieval
```

The retriever does not need an LLM API key. The first real embedding call may
download the Chroma ONNX model. The skill delegates validation to Member 4;
Member 3's actual Pydantic model remains the schema authority.

## Bộ dữ liệu và bàn giao Member 1

Xem [tổng hợp Member 1](docs/member1_handoff.md), [bàn giao Member 4](docs/member1_to_member4_handoff.md) và [bàn giao Member 5](docs/member1_to_member5_handoff.md). Bộ dữ liệu gồm 72 descriptor chunks, 1.800 bài corpus đối chiếu, 84 bài benchmark và 6 basic cases; ảnh Task 1 đi kèm repository.
