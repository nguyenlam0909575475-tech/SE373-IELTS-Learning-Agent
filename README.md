# SE373: IELTS Learning Agent (Đề tài 06)

> **Môn học:** Kỹ nghệ Hệ thống AI Tác tử (Agentic AI Systems Engineering - SE373)  
> **Thời gian:** Học kỳ 1, Năm học 2026–2027  
> **Topic 06:** IELTS Learning Agent (Academic Training Companion)

---

## 1. Giới thiệu tổng quan

**IELTS Learning Agent** là hệ thống AI đồng hành hỗ trợ người học tự luyện thi IELTS Academic qua nhiều bước: kiểm tra đầu vào, chấm bài Writing/Speaking theo tiêu chí Band Descriptors công khai, sinh bài Reading/Listening luyện tập có kiểm chứng, ghi nhớ điểm yếu dài hạn và lập kế hoạch học tập cá nhân hóa.

### Triết lý cốt lõi: Harness-First Architecture
> *"Giá trị của agent nằm ở **harness**, không nằm ở model."*

Thay vì phụ thuộc hoàn toàn vào sinh văn bản tự do của LLM, hệ thống xây dựng một tầng xác thực tất định (**Harness Layer**):
1. **Bảo mật & Cách ly dữ liệu:** Đóng gói văn bản bài làm trong thẻ `<student_essay>`, ngăn chặn Prompt Injection (`injection_detected`).
2. **Không để LLM tính toán:** Số từ và điểm làm tròn IELTS Official (nấc 0.5, quy tắc .25/.75) được tính toán 100% bằng mã Python tất định.
3. **Chống Hallucination:** Mọi nhận xét chấm điểm bắt buộc phải trích dẫn nguyên văn (`verbatim quote`) kèm tọa độ ký tự chính xác `[start_char:end_char]` trong bài viết của thí sinh.
4. **Hội đồng chấm kép & Moderator (UC-07):** Giám khảo A và B chấm độc lập trong ngữ cảnh cô lập; tự động kích hoạt Moderator phân giải khi điểm phân kỳ $> 0.5$ overall hoặc $\ge 1.0$ theo từng tiêu chí.

---

## 2. Bảng phân công nhiệm vụ & Độ phủ K1–K8

Hệ thống được thiết kế đáp ứng đầy đủ **8/8 Knowledge Areas (K1–K8)** theo tiêu chuẩn đánh giá của môn học:

| Thành viên | Horizontal Harness Role (Phase 1) | Owned Use Case(s) | Knowledge Areas Covered |
| :--- | :--- | :--- | :--- |
| **Thành viên 1** | Core Agent Loop, LangGraph State & Retry Detector | **UC-02:** Writing Task 1/2 Grading with Band Descriptors & Citations | **K1** (Loop, Output), **K3** (RAG) |
| **Thành viên 2** | Tool Engineering, RAG Retriever, Plagiarism Sensors | **UC-04:** Reading/Listening Practice Generator with 2-Layer Validator | **K2** (Tools, Skills), **K7** (Verification) |
| **Thành viên 3** | Skill Checks, Rubric Contracts, Committee Workflow | **UC-07:** Dual-Examiner & Moderator Grading Committee | **K6** (Multi-Agent), **K7** (Verification) |
| **Thành viên 4** | LangSmith Tracing, Benchmark & Robustness Eval | **UC-08:** Grading Reliability, Stability & Adversarial Eval Suite | **K7** (Evaluation), **K8** (Security, Obs) |
| **Thành viên 5** | FastAPI Backend, Web UI, Memory & Teacher HITL | **UC-05:** Study Plan with Memory & **UC-10:** Progress Report + Teacher Approval | **K4** (Memory), **K5** (HITL), **K8** (Audit) |

---

## 3. Cấu trúc thư mục dự án

```text
SE373-IELTS-Learning-Agent/
├── .github/workflows/
│   └── ci.yml                                    # GitHub Actions CI (Ruff + Pytest)
├── agent/
│   ├── core/
│   │   ├── state.py                              # [M1] Runtime AgentState
│   │   ├── loop.py                               # [M1] ReAct / LangGraph loop
│   │   ├── detector.py                           # [M1] Loop & stall detector
│   │   └── committee.py                          # [M3] UC-07 Dual-Examiner & Moderator workflow
│   └── tools/
│       ├── compute_tool.py                       # [M2] count_words & compute_band
│       ├── rag_tool.py                           # [M2] retrieve_descriptors (RAG chunk retrieval)
│       ├── plagiarism_tool.py                    # [M2] check_plagiarism against corpus
│       ├── vocab_tool.py                         # [M2] CEFR & SRS vocabulary metrics
│       ├── complexity_tool.py                    # [M2] Sentence complexity metrics
│       └── memory_tool.py                        # [M5] Learner weakness memory
├── skills/
│   ├── writing_assessment/                       # [M3] Skill chấm bài Writing (UC-02, UC-07)
│   │   ├── skill.yaml                            # Định nghĩa hợp đồng I/O & ràng buộc
│   │   ├── instructions.md                       # System prompt phân định vai trò & bảo mật
│   │   └── checks.py                             # Bộ kiểm tra tất định (schema, offset, disclaimer)
│   ├── reading_item_generation/                  # [M2] Skill sinh đề Reading/Listening (UC-04)
│   ├── study_plan/                               # [M5] Skill lập kế hoạch học (UC-05)
│   └── vocab_coach/                              # [M2] Skill học từ vựng (UC-06)
├── backend/                                      # [M5] FastAPI Backend & SSE Streaming
├── frontend/                                     # [M5] Giao diện Web tương tác
├── data/
│   ├── bank/                                     # Ngân hàng đề tự soạn/CC (kèm source & license)
│   ├── knowledge/                                # Dữ liệu RAG band descriptors & lỗi người Việt
│   └── learners/                                 # Hồ sơ người học giả lập
├── evals/                                        # [M4] Benchmark chấm điểm & adversarial attacks
├── tests/                                        # Bộ unit tests cho tools và skills
├── AGENTS.md                                     # Đặc tả kiến trúc Multi-Agent & Harness
├── TEAM_NOTICE.md                                # Hướng dẫn phối hợp nhóm & quy ước file placeholder
├── Phase_1_Process_and_Tasks.md                   # Bản kế hoạch chi tiết Phase 1
├── requirements.txt                              # Danh sách thư viện Python
└── pyproject.toml                                # Cấu hình môi trường pytest & ruff
```

> ⚠️ **Lưu ý về các file placeholder:** Các file rỗng (0 bytes) trong repo đã được tạo sẵn để cố định cấu trúc import. Vui lòng đọc kĩ [TEAM_NOTICE.md](TEAM_NOTICE.md) trước khi chỉnh sửa.

---

## 4. Hướng dẫn cài đặt & Kiểm thử

### Yêu cầu tiên quyết
* Python 3.10 trở lên (khuyến nghị Python 3.11 hoặc 3.12).
* Git.

### Cài đặt môi trường
```bash
# 1. Clone repository
git clone https://github.com/nguyenlam0909575475-tech/SE373-IELTS-Learning-Agent.git
cd SE373-IELTS-Learning-Agent

# 2. Tạo và kích hoạt môi trường ảo (Virtualenv)
python -m venv .venv
# Trên Windows PowerShell:
.venv\Scripts\Activate.ps1
# Trên Linux/macOS:
source .venv/bin/activate

# 3. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

### Chạy kiểm tra & Linter
```bash
# Kiểm tra code style & linter với Ruff
ruff check .

# Chạy toàn bộ Unit Tests
pytest
```

---

## 5. Quy định bắt buộc của đề tài (Compliance Rules)

Mọi đóng góp vào repository phải tuân thủ nghiêm ngặt 4 quy tắc sau:
1. **Không sao chép đề có bản quyền:** Tuyệt đối không dùng đề từ sách Cambridge IELTS hoặc tài liệu thương mại. Mọi đề thi trong `data/bank/` bắt buộc phải có 2 trường `source` và `license`.
2. **Nhãn ước lượng điểm do AI chấm:** Mọi kết quả chấm Writing/Speaking hiển thị cho người học bắt buộc phải kèm disclaimer:
   > *"Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức."*
3. **Bảo vệ dữ liệu người học:** Chỉ sử dụng hồ sơ người học giả lập (`data/learners/simulated_learners.json`). Tuyệt đối không commit dữ liệu cá nhân, bài làm thật của người dùng vào repo.
4. **Tự xây dựng Agent:** Sử dụng mô hình qua API kết hợp LangGraph/LangChain; cấm sử dụng các API chấm bài IELTS đóng gói sẵn của bên thứ ba.
