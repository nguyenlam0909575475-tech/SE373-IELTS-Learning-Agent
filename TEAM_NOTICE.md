# HƯỚNG DẪN PHỐI HỢP NHÓM & QUY ƯỚC KỸ THUẬT (PHASE 1)

> **Dành cho:** Toàn bộ thành viên nhóm Đề tài 06 (SE373 — IELTS Learning Agent)  
> **Căn cứ chính thức:** [`docs/Phan_Cong_Nhiem_Vu_Phase_1.md`](docs/Phan_Cong_Nhiem_Vu_Phase_1.md) và [`docs/Grading Criteria for the Final Project.md`](docs/Grading%20Criteria%20for%20the%20Final%20Project.md)  
> **Ghi chú quan trọng:** Tài liệu này thay thế hoàn toàn bảng phân công sơ khai trong các bản nháp trước.

---

## 1. Phân biệt phạm vi: Phase 1 vs. Toàn đồ án

* **Phase 1 (Trọng tâm UC-02):**
  Cả 5 thành viên cùng chung sức hoàn thiện một Use Case nền móng: **UC-02 — Chấm Writing Task 1/Task 2 theo Band Descriptors, có dẫn chứng**.
  Nhiệm vụ được phân chia theo **5 vai trò ngang trong Harness Pipeline** (Data $\rightarrow$ Retrieval $\rightarrow$ Core Agent $\rightarrow$ Tools/Validators $\rightarrow$ App UI/Eval Runner).
* **Toàn đồ án (Final Project - K1 đến K8):**
  Mỗi thành viên sẽ sở hữu ít nhất một Use Case độc lập để bảo đảm độ phủ toàn diện 8 mảng kiến thức:
  * **Thành viên 1:** **UC-02** — Writing Grading Engine (K1, K3).
  * **Thành viên 2:** **UC-04** — Reading/Listening Practice Generator với Validator 2 lớp (K2, K7).
  * **Thành viên 3:** **UC-07** — Dual-Examiner & Moderator Grading Committee (K6, K7).
  * **Thành viên 4:** **UC-08** — Grading Reliability, Stability & Adversarial Eval Suite (K7, K8).
  * **Thành viên 5:** **UC-05** — Study Plan with Weakness Memory & **UC-10** — Progress Report + Teacher HITL (K4, K5, K8).

---

## 2. Bảng phân quyền sở hữu File & Nhiệm vụ Phase 1

Để tránh xung đột Git (merge conflicts) khi phát triển song song, mỗi thành viên chịu trách nhiệm chính trên các thư mục/file sau:

| Thành viên | Trọng tâm Phase 1 (UC-02) | File & Thư mục sở hữu chính |
| :--- | :--- | :--- |
| **👤 Người 1** | **Knowledge Base & Ingestion:** Thu thập IELTS Band Descriptors chính thức (đủ 6 metadata chuẩn), viết script `rebuild_vectorstore.py`, thu thập tập benchmark $\ge 30$ bài và 5 test cases cơ bản. | `scripts/rebuild_vectorstore.py`<br>`data/bank/`<br>`data/corpus_plagiarism/`<br>`evals/data/5_basic_cases.json`<br>`docs/data_sources.md` |
| **👤 Người 2** | **RAG Retrieval & Skill Package:** Xây dựng tool `retrieve_descriptors` với bộ lọc cứng (Task 1 tuyệt đối không lấy nhầm Task 2), đóng gói thư mục Skill `skills/writing-assessment/`, đo Precision/Recall của RAG. | `agent/tools/rag_tool.py` (hoặc `src/tools/rag_descriptors.py`)<br>`skills/writing-assessment/`<br>`tests/test_retrieval.py` |
| **👤 Người 3** | **Writing Examiner Agent Core:** Thiết kế Pydantic Schema SSOT `WritingAssessment`, xây dựng StateGraph Agent Loop (LangGraph), cơ chế tự sửa lỗi Self-Correction retry tối đa 2 lần. | `agent/core/` (`loop.py`, `state.py`, `schemas.py`)<br>`agent/core/committee.py` |
| **👤 Người 4** | **Deterministic Tools, Validators & CI/CD:** Viết 3 tools code xác định (`count_words`, `compute_band`, `check_plagiarism`), bộ kiểm tra `quote_validator` (100% nguyên văn và tọa độ), `refs_validator`, kiểm tra an toàn và GitHub Actions CI. | `agent/tools/` (`compute_tool.py`, `plagiarism_tool.py`, `security_tool.py`)<br>`skills/writing_assessment/validators.py`<br>`.github/workflows/ci.yml`<br>`tests/test_validators.py` |
| **👤 Người 5** | **Application, Automated Eval Runner & Demo:** Xây dựng FastAPI Backend, Web App UI (Interactive Highlighting dẫn chứng, realtime counter, đồng hồ đếm ngược, disclaimer), biến công tắc `USE_MOCK_AGENT`, script `evals/run.py` và video demo. | `backend/` (`main.py`, `config.py`, `mock_service.py`, `live_service.py`)<br>`frontend/` (`index.html`, `style.css`, `app.js`)<br>`evals/run.py`<br>`eval_results.json`<br>`evals/eval_report_phase1.md` |

---

## 3. Các quy ước kỹ thuật dùng chung đã chốt (Mandatory Contracts)

1. **Biểu thức Regex đếm từ dùng chung (Frontend, Backend, Tools):**
   ```python
   WORD_COUNT_REGEX = r"\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b"
   ```
   *Bắt buộc dùng chung regex này ở mọi nơi để tránh việc Frontend hiển thị 150 từ nhưng Backend lại đếm 149 từ.*
2. **Quy ước tọa độ trích dẫn bằng chứng (Evidence Offsets):**
   * Chỉ số bắt đầu từ `0`, `end_char` loại trừ, bảo đảm:
     ```python
     essay_text[start_char:end_char] == quote
     ```
   * Dẫn chứng phải là câu văn có thật 100% nguyên văn trong bài làm của học viên, không được sinh tự do hay biến tấu.
3. **Luật làm tròn điểm bài Task (`compute_band`):**
   * Tính trung bình 4 tiêu chí, làm tròn đến nấc `0.5` gần nhất: `.25` lên `.5`, `.75` lên `1.0`. Code tính toán 100%, không để LLM tự tính.
4. **Ràng buộc bài Lạc đề (`off_topic`):**
   * Bài bị gắn cờ `off_topic` bắt buộc điểm `task_achievement` (Task 1) hoặc `task_response` (Task 2) phải $\le 5.0$.
5. **Dòng cảnh báo ước lượng điểm do AI chấm (Bắt buộc theo Rule 1.5.2):**
   * Mọi màn hình UI và file báo cáo phải hiển thị rõ:
     > *"Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức."*
6. **Biến công tắc Mock Agent (`USE_MOCK_AGENT`):**
   * Trong `.env`: `USE_MOCK_AGENT="true"` để chạy chế độ giả lập offline đạt chuẩn Harness, `USE_MOCK_AGENT="false"` để gọi LLM Agent thực tế.
   * Trên Web UI: Có công tắc gạt trực tiếp `[Mock Agent: ON / OFF]` để chuyển đổi tức thời.

---

## 4. Quy trình làm việc với Git & Bảo mật

1. **Không commit lên `main`:** Luôn tạo nhánh riêng từ `main` theo cú pháp chuẩn:
   * Người 1: `member1-IELTS-Band-Descriptors-Data&Script`
   * Người 2: `feat/member2-retrieval-skill`
   * Người 3: `feature/m3-agent-core`
   * Người 4: `feature/m4-tools`
   * Người 5: `feature/m5-app-ui-and-eval`
2. **Bảo mật Secret & API Key:**
   * Tuyệt đối **KHÔNG commit file `.env` thật**, API key, token lên GitHub.
   * Chỉ commit file mẫu [`.env.example`](.env.example) không chứa secret.
   * Trước khi commit, kiểm tra trạng thái bằng `git status`.
3. **Kiểm tra tự động trước khi đẩy code (Pre-push check):**
   ```bash
   # Kiểm tra style và cú pháp
   ruff check .

   # Chạy toàn bộ unit test
   pytest
   ```
