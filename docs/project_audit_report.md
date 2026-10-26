# BÁO CÁO RÀ SOÁT VÀ ĐÁNH GIÁ CHI TIẾT THIẾU SÓT ĐỒ ÁN (PROJECT GAP ANALYSIS & AUDIT REPORT)

> **Học phần:** SE373 — Agentic AI Systems Engineering  
> **Đề tài 06:** IELTS Learning Agent (Hệ thống Multi-Agent hỗ trợ tự luyện thi IELTS Academic)  
> **Thời điểm rà soát:** 25/10/2026  
> **Căn cứ đối chiếu kỹ thuật & quy chế:**  
> 1. `Grading Criteria for the Final Project.md` (Đề cương & Thang điểm chính thức của Giảng viên)  
> 2. `docs/Phan_Cong_Nhiem_Vu_Phase_1.md` (Bản phân công nhiệm vụ chi tiết Phase 1)  
> 3. `Repo/tai lieu tham khao/huong_dan_ticket_va_pr.md` (Quy chuẩn Git Flow, Sub-issues & Project Board)  
> 4. `AGENTS.md` & `TEAM_NOTICE.md` (Quy chuẩn Harness-First, Anti-Hallucination & Safe Evaluation)

---

## MỤC LỤC
1. [TỔNG QUAN TIẾN ĐỘ & BẢNG ĐIỂM NÓNG (EXECUTIVE SUMMARY)](#1-tổng-quan-tiến-độ--bảng-điểm-nóng-executive-summary)
2. [RÀ SOÁT PHẦN VIỆC CỦA BẠN (NGƯỜI 3 — AGENT CORE)](#2-rà-soát-phần-việc-của-bạn-người-3--agent-core)
3. [RÀ SOÁT TIẾN ĐỘ PHASE 1 TOÀN NHÓM (5 THÀNH VIÊN)](#3-rà-soát-tiến-độ-phase-1-toàn-nhóm-5-thành-viên)
4. [RÀ SOÁT CÁC QUY ĐỊNH BẮT BUỘC ĐỂ KHÔNG BỊ TRỪ ĐIỂM (DISQUALIFIERS)](#4-rà-soát-các-quy-định-bắt-buộc-để-không-bị-trừ-điểm-disqualifiers)
5. [RÀ SOÁT TOÀN DIỆN CUỐI KỲ (PHASE 2 — TOÀN BỘ K1 ĐẾN K8 & 11 USE CASES)](#5-rà-soát-toàn-diện-cuối-kỳ-phase-2--toàn-bộ-k1-đến-k8--11-use-cases)
6. [MA TRẬN PHÂN CÔNG GỢI Ý CHO PHASE 2 ĐỂ ĐẠT ĐIỂM TỐI ĐA (10.0/10.0)](#6-ma-trận-phân-công-gợi-ý-cho-phase-2-để-đạt-điểm-tối-đa-100100)
7. [KẾ HOẠCH HÀNH ĐỘNG CỤ THỂ (ACTION PLAN)](#7-kế-hoạch-hành-động-cụ-thể-action-plan)

---

## 1. TỔNG QUAN TIẾN ĐỘ & BẢNG ĐIỂM NÓNG (EXECUTIVE SUMMARY)

### 📊 Bảng đối soát nhanh theo các mốc nghiệm thu:

| Hạng mục kiểm tra | Yêu cầu chuẩn | Hiện trạng thực tế trong Repo | Mức độ rủi ro |
| :--- | :--- | :--- | :---: |
| **Nhánh chính `main` trên GitHub** | Phải hội tụ đủ code của cả 5 thành viên qua PR | Đã merge PR của 4 bạn (#1, #4, #7, #9, #10). **Chưa có PR của Người 3 (Khanh)** | 🔴 **Khẩn cấp** |
| **Agent Core & Live LLM (UC-02)** | LangGraph loop, Verbatim evidence, Bounded retry | **Đã hoàn thành xuất sắc**, test pass 13/13 unit tests, live demo thành công | 🟢 **Hoàn thành** |
| **Ngân hàng đề (`data/bank/`)** | $\ge 10$ Task 1, $\ge 10$ Task 2 (đủ metadata `source`, `license`) | Mới có 2 đề Task 1 và 1 đề Task 2 | 🟡 **Thiếu số lượng** |
| **Kết quả Đánh giá tự động (`evals/`)** | File `eval_results.json` ghi nhận số liệu thực thi | Hiện tại file kết quả đang ghi `execution_mode: "mock"` | 🟡 **Cần chạy live** |
| **Release Tag Phase 1** | Tag `v0.1-phase1` trên commit cuối của `main` | Chưa tạo tag | 🔴 **Chưa có** |
| **Video Demo Phase 1** | Thời lượng $\le 15$ phút, demo web, realtime word count, highlight dẫn chứng | Chưa có video nộp bài | 🔴 **Chưa có** |
| **Phạm vi Phase 2 (Cuối kỳ)** | 5-7 Use Cases phủ đủ 8 mảng K1–K8, 1 External Tool thật, $\ge 2$ Skills | Mới hoàn thành UC-02 và 1 Skill (`writing-assessment`) | ⚪ **Kế hoạch Phase 2** |

---

## 2. RÀ SOÁT PHẦN VIỆC CỦA BẠN (NGƯỜI 3 — AGENT CORE)

### ✅ Những gì BẠN ĐÃ LÀM HOÀN CHỈNH:
1. **Pydantic SSOT Schema (`WritingAssessment`):**
   * Định nghĩa tại [src/agent/schemas.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/src/agent/schemas.py).
   * Tự động nhận diện tiêu chí theo chuẩn IELTS Academic: `task_achievement` cho Task 1 và `task_response` cho Task 2.
   * Ràng buộc chặt chẽ: `word_count` và `overall_band` tính toán bằng code Python tất định, không để LLM tự tính.
2. **LangGraph StateGraph Workflow:**
   * Triển khai tại [src/agent/graph.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/src/agent/graph.py) và [src/agent/nodes.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/src/agent/nodes.py).
   * Chuỗi chuyển tiếp trạng thái xác định: `resolve_task` $\rightarrow$ `prepare_tools` $\rightarrow$ `retrieve_rubric` $\rightarrow$ `examiner` $\rightarrow$ `verify` $\rightarrow$ `finalize` / `failure`.
3. **Cơ chế Tự sửa sai có chặn trên (Bounded Self-Correction Retry):**
   * Giới hạn tối đa 2 lần retry (tổng tối đa 3 lần gọi LLM) khi gặp lỗi schema, quote không khớp, hoặc mâu thuẫn cờ.
   * Tự động trả về JSON lỗi có cấu trúc (`ASSESSMENT_VALIDATION_FAILED`), tuyệt đối không để kết quả sai hiển thị lên UI.
4. **Kiểm soát Dẫn chứng Nguyên văn & Căn chỉnh Tọa độ Ký tự:**
   * Tự động căn chỉnh lại `[start_char:end_char]` trong `nodes.py:verify` để chống lệch vị trí giữa phỏng đoán của LLM và chuỗi văn bản gốc.
5. **Khả năng chạy Live LLM thực tế:**
   * Đã tích hợp adapter OpenAI-compatible ([src/agent/openai_compatible.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/src/agent/openai_compatible.py)) và Gemini ([src/agent/gemini.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/src/agent/gemini.py)).
   * Đã chạy kiểm thử thực tế thành công với mô hình `qwen/qwen3.8-27b` trên đề thi dân số Chile Task 1 do bạn cung cấp.
6. **Bộ Unit Tests hoàn chỉnh:**
   * File [tests/test_agent_core.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/tests/test_agent_core.py) gồm 6 test cases bao quát toàn diện luồng StateGraph, retry kiệt sức, và schema validation. Pass 100%.

---

### ❌ Những gì BẠN ĐANG THIẾU CẦN THỰC HIỆN NGAY:

#### 1. Code mới nhất chưa được Commit lên Git (Unstaged changes)
* **Hiện trạng:**
  * Các file bạn đã sửa và tạo mới: `backend/live_service.py`, `src/agent/nodes.py`, `src/agent/mock_services.py`, `src/agent/openai_compatible.py`, `src/agent/gemini.py`, `src/agent/provider_errors.py`, `examples/run_live_demo.py`, `examples/fixtures/my_task1.json` đang nằm ở trạng thái *Changes not staged* hoặc *Untracked*.
* **Hậu quả:** Nếu máy tính gặp sự cố hoặc chuyển sang máy khác, toàn bộ phần tích hợp Live LLM và đề thi mới sẽ bị mất.

#### 2. Nhánh của bạn chưa mở Pull Request và chưa được Merge vào `main`
* **Hiện trạng:**
  * Nhánh `feat/khanh/agent-core-loop` của bạn đang đứng độc lập.
  * Nhánh `origin/main` hiện tại **hoàn toàn chưa có phần Agent Core hoàn chỉnh của bạn**.
* **Hậu quả:** Giảng viên hoặc các thành viên khác khi clone nhánh `main` về sẽ thấy thiếu phần Core của bạn, có thể dẫn đến việc bạn bị đánh giá là chưa nộp bài.

#### 3. Chưa đóng Sub-issue trên GitHub Project Board
* **Hiện trạng:** Theo tài liệu [huong_dan_ticket_va_pr.md](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/tai%20lieu%20tham%20khao/huong_dan_ticket_va_pr.md), bạn phụ trách:
  * Sub-issue 3A: Xây dựng Core Loop & Schema SSOT
  * Sub-issue 3B: Bounded Verification & Retry
* **Cần làm:** Khi mở Pull Request, phải chèn cú pháp:
  `Closes #<id_sub_issue_3A>, Closes #<id_sub_issue_3B>` để Project Board tự động chuyển sang `Done` (2/2 completed).

---

## 3. RÀ SOÁT TIẾN ĐỘ PHASE 1 TOÀN NHÓM (5 THÀNH VIÊN)

Căn cứ vào `docs/Phan_Cong_Nhiem_Vu_Phase_1.md`:

### 👤 Người 1: Knowledge Base & Data Governance
* **Đã có:**
  * Script [scripts/rebuild_vectorstore.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/scripts/rebuild_vectorstore.py).
  * Bộ benchmark 30 bài [evals/writing_benchmark_30.json](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/evals/writing_benchmark_30.json).
  * Tài liệu nguồn gốc dữ liệu [docs/data_sources.md](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/docs/data_sources.md).
* **Thiếu sót:**
  * Ngân hàng đề trong `data/bank/`: Hiện mới có 2 bài Task 1 và 1 bài Task 2. Đề tài yêu cầu tối thiểu **10 đề Writing Task 1** (có dữ liệu bảng text) và **10 đề Writing Task 2** (đủ các dạng).
  * Mỗi đề trong `data/bank/` bắt buộc phải có 2 trường: `source` và `license`.

### 👤 Người 2: RAG Retrieval & Skill Specification
* **Đã có:**
  * Tool truy xuất [src/tools/rag_descriptors.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/src/tools/rag_descriptors.py) có bộ lọc metadata cứng (`test_part`, `criterion`).
  * Gói Skill chuẩn [skills/writing-assessment/](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/skills/writing-assessment/) gồm `skill.yaml`, `instructions.md`, `checks.py`.
* **Thiếu sót:**
  * Báo cáo đánh giá chất lượng RAG độc lập (`member2_rag_skill_report.md` đã có nhưng cần đối chiếu lại khi nạp đầy đủ dữ liệu mới).

### 👤 Người 4: Deterministic Tools, Validators & CI/CD
* **Đã có:**
  * Bộ công cụ tất định trong `agent/tools/`: `compute_tool.py` (`count_words`, `compute_band`), `plagiarism_tool.py`, `security_tool.py`.
  * Bộ validators trong `skills/writing_assessment/validators.py`: `quote_validator`, `refs_validator`, `consistency_validator`.
  * Luồng CI tự động [.github/workflows/ci.yml](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/.github/workflows/ci.yml).
* **Thiếu sót:**
  * Cần đảm bảo các test của Người 4 phủ cả 2 ca biên độ dài: `case_03a_task1_under_length` (< 150 từ) và `case_03b_task2_under_length` (< 250 từ).

### 👤 Người 5: Web UI, Eval Runner & Package Release
* **Đã có:**
  * Giao diện Web đẹp mắt tại `frontend/` (`index.html`, `style.css`, `app.js`).
  * Bộ đếm từ trực tiếp, đồng hồ đếm ngược, tô màu highlight dẫn chứng tương tác.
  * Bộ chạy đánh giá [evals/run.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/evals/run.py).
* **Thiếu sót:**
  * **Chạy đánh giá thật:** File [eval_results.json](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/eval_results.json) hiện tại đang chạy ở chế độ `MOCK`. Cần chạy một lượt đánh giá kết hợp Live LLM hoặc ghi rõ lý do mock để xuất báo cáo chính thức.
  * **Kết nối Live Service:** Kết nối giao diện web trực tiếp vào [backend/live_service.py](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/backend/live_service.py) để người dùng có thể chọn chế độ chấm thật bằng LLM.
  * **Git Release Tag:** Chưa tạo tag `v0.1-phase1`.
  * **Video Demo Phase 1:** Chưa quay video demo thời lượng $\le 15$ phút theo yêu cầu nộp bài.

---

## 4. RÀ SOÁT CÁC QUY ĐỊNH BẮT BUỘC ĐỂ KHÔNG BỊ TRỪ ĐIỂM (DISQUALIFIERS)

Căn cứ theo **Mục 1.5 trong file Grading Criteria**:

| STT | Quy định bắt buộc | Mức phạt nếu vi phạm | Trạng thái hiện tại | Đánh giá |
| :---: | :--- | :--- | :---: | :---: |
| **1** | **Không sao chép tài liệu có bản quyền**<br>Cấm dùng đề, bài mẫu từ sách Cambridge IELTS hoặc khóa học trả phí. Mỗi đề trong ngân hàng phải có `source` và `license`. | Vi phạm thì mọi UC dùng mục đề đó bị **0 điểm**. | Đã tuân thủ | 🟢 **Đạt** |
| **2** | **Nhãn cảnh báo điểm ước lượng AI**<br>Mọi màn hình Web, báo cáo, file xuất phải có câu: *"Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức"*. | Vi phạm thì tiêu chí U1 của UC liên quan tối đa mức **Trung bình**. | Đã có trên Web và Schema | 🟢 **Đạt** |
| **3** | **Bộ dữ liệu điểm chuẩn phải có nguồn hợp lệ**<br>Lấy từ bài mẫu công khai có nhận xét giám khảo hoặc do giáo viên chấm (ghi rõ link/tên). Cấm dùng LLM gán điểm chuẩn. | Vi phạm thì **UC-08 bị 0 điểm**, và mọi chỉ số độ chính xác chấm điểm không được công nhận. | Benchmark 30 bài có dẫn nguồn trong `docs/data_sources.md` | 🟢 **Đạt** |
| **4** | **Bảo vệ dữ liệu người học (PII)**<br>Không commit bài làm thật, họ tên, email, hay audio thật của học viên vào repo. Trace chỉ chứa dữ liệu giả lập. | Commit dữ liệu thật bị **trừ 1,0 điểm tổng** vào điểm đồ án. | File trace thật đã được ignore, chỉ giữ mock samples | 🟢 **Đạt** |
| **5** | **Nhóm phải tự xây dựng Agent**<br>Không dùng API chấm điểm đóng gói sẵn của bên thứ ba. Sử dụng LangGraph / LangChain và LLM raw. | Vi phạm thì mọi UC dùng thành phần đó bị **0 điểm**. | Tự viết StateGraph hoàn toàn bằng Python | 🟢 **Đạt** |
| **6** | **Không để rò rỉ mã bí mật (Secret API Keys)**<br>Không commit API Key vào Git, source code, test hay file log. | Trừ điểm nặng theo quy chế môn học. | Đã quét bằng `check_repository.py`, file `.env` đã được ignore | 🟢 **Đạt** |

---

## 5. RÀ SOÁT TOÀN DIỆN CUỐI KỲ (PHASE 2 — TOÀN BỘ K1 ĐẾN K8 & 11 USE CASES)

Trong kỳ thi cuối kỳ, đồ án được chấm tối đa 10 điểm (Phần Agent: 7.5 điểm, Phần Ứng dụng: 2.5 điểm). Nhóm phải chọn làm từ **5 đến 7 Use Cases** sao cho phủ đủ **8 mảng kiến thức K1 đến K8**.

### 📌 Hiện trạng triển khai 11 Use Cases:

```
[Danh sách 11 Use Cases của Đề tài 06]
  ├── UC-01: Kiểm tra đầu vào & ước lượng trình độ 4 kỹ năng [K1, K5] ──► 🔴 Chưa làm
  ├── UC-02: Chấm Writing Task 1/2 có dẫn chứng & RAG [K1, K3] ─────────► 🟢 Hoàn thành (Phase 1)
  ├── UC-03: Speaking Mock Test 3 phần đào sâu [K1, K3, K4] ────────────► 🔴 Chưa làm
  ├── UC-04: Sinh bài Reading/Listening có kiểm chứng 2 lớp [K2, K7] ───► 🔴 Chưa làm
  ├── UC-05: Kế hoạch học cá nhân hoá & Bộ nhớ điểm yếu [K4, K5] ───────► 🔴 Chưa làm
  ├── UC-06: Ôn từ vựng lặp ngắt quãng SRS qua Tool [K2, K4] ───────────► 🔴 Chưa làm
  ├── UC-07: Hội đồng chấm 2 giám khảo & Moderator [K6, K7] ───────────► 🟡 Đã có khung (cần nối LangGraph)
  ├── UC-08: Bộ đánh giá độ tin cậy, ổn định & độ bền [K7, K8] ─────────► 🟡 Đã có SecurityGuard (cần QWK/3x loop)
  ├── UC-09: Phiên thi thử dài có Checkpointer Resume [K4, K5] ─────────► 🔴 Chưa làm
  ├── UC-10: Báo cáo tiến bộ & Human-in-the-loop duyệt điểm [K5, K8] ────► 🔴 Chưa làm
  └── UC-11: MCP Server ngân hàng đề "ielts-bank" [K6, K8] ─────────────► 🔴 Chưa làm
```

---

### 🔍 Chi tiết các yêu cầu kỹ thuật còn thiếu cho Phase 2:

#### 1. Thiếu Tích hợp Công cụ ngoài thật sự (External Real Tool — Mục 4.1)
* **Quy định đề bài:** *"Ít nhất 1 tool phải là công cụ ngoài thật sự: STT/TTS API, MCP server, cơ sở dữ liệu thật, hoặc thư viện kiểm tra ngữ pháp (ví dụ LanguageTool)"*.
* **Hiện trạng:** Nhóm đang dùng các hàm tính toán nội bộ Python (`count_words`, `compute_band`) và API LLM.
* **Cần bổ sung:**
  * Tích hợp **LanguageTool API / cục bộ** vào khâu phân tích ngữ pháp, HOẶC
  * Triển khai **MCP Server `ielts-bank`** (UC-11), HOẶC
  * Tích hợp **Whisper STT / TTS API** cho phần Speaking (UC-03).

#### 2. Thiếu Reusable Skills thứ hai (Mục 4.2)
* **Quy định đề bài:** Toàn hệ thống cần ít nhất **2 skills tái sử dụng được**, có contract đầy đủ (`skill.yaml`, `instructions.md`, `checks.py`).
* **Hiện trạng:** Mới có 1 skill là [skills/writing-assessment/](file:///d:/Obsidian%20Vault/Flow/03-Projects/HK_V/SE373_Agentic%20AI/Đồ%20Án/Repo/SE373-IELTS-Learning-Agent/skills/writing-assessment/).
* **Cần bổ sung:** Thêm 1 trong các skill sau:
  * `vocab-coach` (cho UC-06).
  * `reading-item-generation` (cho UC-04).
  * `speaking-examiner` (cho UC-03).

#### 3. Thiếu Ngân hàng dữ liệu toàn diện (Mục 2.1 & 2.3)
Cho giai đoạn hoàn chỉnh, nhóm cần chuẩn bị bổ sung:
* **Speaking:** 10 bộ chủ đề (Part 1, Part 2 cue card, Part 3).
* **Reading:** 6 bài đọc (600–900 từ, 8–13 câu hỏi, tối thiểu 3 dạng câu hỏi).
* **Listening:** 4 script (400–700 từ, 8–10 câu hỏi).
* **Hồ sơ người học giả lập:** Ít nhất 10 hồ sơ với lịch sử học tập (cho UC-01 và UC-05).
* **Bộ câu hỏi kiểm tra validator:** Ít nhất 40 câu có đáp án do người kiểm (có câu cố tình cài sai đáp án để kiểm tra validator của UC-04).

#### 4. Thiếu Giao diện người dùng cho các tính năng mở rộng (Mục 5)
* Hiện tại Frontend chỉ mới phục vụ bài thi Writing (UC-02).
* Khi nộp toàn đồ án, nếu làm các UC khác thì Web App cần có thêm:
  * **UC-07:** Giao diện hiển thị điểm của từng giám khảo (Examiner A, B) và quyết định phân giải của Moderator.
  * **UC-05 & UC-06:** Màn hình xem lộ trình học và flashcard ôn từ vựng SRS.
  * **UC-10:** Dashboard dành cho Giáo viên để bấm nút: **Duyệt điểm / Chỉnh sửa / Từ chối**.

---

## 6. MA TRẬN PHÂN CÔNG GỢI Ý CHO PHASE 2 ĐỂ ĐẠT ĐIỂM TỐI ĐA (10.0/10.0)

Để đạt điểm tuyệt đối 7.5 phần Agent, nhóm cần thực hiện **5 Use Cases** và phải phủ đủ **8 mảng kiến thức K1–K8** (mỗi thành viên sở hữu chính 1 Use Case):

| Thành viên | Use Case đề xuất sở hữu | Mảng K chính | Trách nhiệm cốt lõi trong Phase 2 |
| :--- | :---: | :---: | :--- |
| **Người 1** | **UC-04: Sinh bài Reading/Listening** | **K2, K7** | Viết generator sinh đề và validator 2 lớp (rule + solver agent). Xây dựng skill `reading-item-generation`. |
| **Người 2** | **UC-06: Ôn từ vựng SRS qua Tool** | **K2, K4** | Xây dựng thuật toán SM-2, hệ thống flashcard lặp ngắt quãng, đóng gói skill `vocab-coach`. |
| **Người 3 (Bạn)** | **UC-07: Hội đồng chấm thi & Moderator** | **K6, K7** | Hoàn thiện luồng Multi-Agent Examiner A & B độc lập, điều phối Moderator khi điểm lệch > 0.5, ghi trace phối hợp. |
| **Người 4** | **UC-08: Đánh giá độ tin cậy & bền bỉ** | **K7, K8** | Xây dựng script 1 lệnh đo MAE, QWK $\ge 0.6$, test lặp 3 lần, và bộ 5+ ca tấn công adversarial. |
| **Người 5** | **UC-10: Báo cáo tiến bộ & Human-in-the-loop** | **K5, K8** | Xây dựng cơ chế ngắt workflow chờ giáo viên duyệt (LangGraph interrupt), màn hình dashboard giáo viên. |

> **Kiểm tra độ phủ K1–K8:**
> * UC-02 (đã làm ở Phase 1): Phủ **K1, K3**
> * UC-04: Phủ **K2, K7**
> * UC-06: Phủ **K2, K4**
> * UC-07: Phủ **K6, K7**
> * UC-08: Phủ **K7, K8**
> * UC-10: Phủ **K5, K8**
> $\Rightarrow$ **Phủ trọn vẹn 100% từ K1 đến K8, không bị trừ bất kỳ 0.5 điểm nào về độ phủ kiến thức!**

---

## 7. KẾ HOẠCH HÀNH ĐỘNG CỤ THỂ (ACTION PLAN)

### 🎯 PHẦN VIỆC CẤP BÁCH CỦA BẠN (NGƯỜI 3) HÔM NAY:

#### Bước 1: Kiểm tra nhánh hiện tại
Đảm bảo bạn đang ở nhánh `feat/khanh/agent-core-loop`:
```powershell
git branch
```

#### Bước 2: Commit toàn bộ các cải tiến mới
Đưa toàn bộ phần tích hợp Live LLM, mock services và các file tài liệu vào Git:
```powershell
git add backend/live_service.py src/agent/ mock_services.py src/agent/nodes.py src/agent/openai_compatible.py src/agent/gemini.py src/agent/provider_errors.py examples/ docs/ tests/ data/bank/
git commit -m "feat(agent): finalize live llm integration, verification retry, and unit tests"
```

#### Bước 3: Đẩy nhánh lên GitHub (Bạn tự thực hiện trên Terminal)
```powershell
git push origin feat/khanh/agent-core-loop
```

#### Bước 4: Mở Pull Request vào nhánh `main`
* Lên giao diện GitHub của Repo: `nguyenlam0909575475-tech/SE373-IELTS-Learning-Agent`.
* Bấm **New Pull Request**:
  * Base: `main` $\leftarrow$ Compare: `feat/khanh/agent-core-loop`.
  * Tiêu đề: `feat(agent): LangGraph Agent Core Loop, Schema SSOT & Verification Retry (UC-02)`
  * Nội dung: Ghi chú bàn giao, trích dẫn `Closes #<id_sub_issue_3A>` và `Closes #<id_sub_issue_3B>`.
  * Gán reviewer: Chọn trưởng nhóm hoặc thành viên khác duyệt.
* Khi CI Actions báo xanh (All checks passed), tiến hành **Merge Pull Request**.

---

### 👥 PHẦN VIỆC CẢ NHÓM CẦN HOÀN THIỆN ĐỂ NỘP PHASE 1:

1. **Bổ sung đề vào `data/bank/`:** Mỗi bạn trong nhóm soạn thêm 2 đề Task 1 và 2 đề Task 2 (có bảng số liệu text, metadata `source` và `license`) để đạt đủ tối thiểu 10 đề mỗi loại.
2. **Chạy chính thức Eval Runner:** Người 5 chạy script `python -m evals.run` kết hợp với Agent thật để cập nhật file `eval_results.json` và `evals/eval_report_phase1.md` với số liệu Live LLM thật.
3. **Tạo Release Tag `v0.1-phase1`:** Sau khi merge đủ PR của bạn vào `main`:
   ```powershell
   git checkout main
   git pull origin main
   git tag -a v0.1-phase1 -m "Release Phase 1: IELTS Writing Assessment Core (UC-02)"
   git push origin v0.1-phase1
   ```
4. **Quay Video Demo Phase 1:** Quay video $\le 15$ phút thể hiện:
   * Trình soạn thảo và đếm từ realtime trên Web.
   * Gửi bài làm sang Backend, Agent Core gọi LLM thật chấm điểm.
   * Kết quả trả về với câu cảnh báo disclaimer và tính năng click tiêu chí để **tô màu highlight câu dẫn chứng nguyên văn** trên bài làm.
   * Bằng chứng chạy pass toàn bộ bộ kiểm thử tự động.
