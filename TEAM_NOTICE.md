# THÔNG BÁO QUAN TRỌNG VỀ CẤU TRÚC REPO & HƯỚNG DẪN PHỐI HỢP NHÓM (PHASE 1)

> **Dành cho:** Toàn bộ thành viên nhóm Đề tài 06 (SE373 - IELTS Learning Agent)  
> **Mục đích:** Đồng bộ quy ước cấu trúc dự án, giải thích các file placeholder rỗng, và ngăn ngừa xung đột (merge conflicts) khi kéo mã nguồn về máy.

---

## 1. Giải thích về các File Placeholder (File Rỗng 0 Bytes)

Trong PR #2, cấu trúc thư mục của toàn bộ dự án đã được định hình sẵn theo chuẩn kiến trúc nộp đồ án (Rubric & Architecture Tree). Các file trong:
* `agent/tools/*.py` (`bank_tool.py`, `compute_tool.py`, `plagiarism_tool.py`, `rag_tool.py`, `memory_tool.py`...)
* `backend/*.py` (`main.py`...)
* `data/**/*.json` (`bank/`, `knowledge/`, `learners/`)
* `evals/*.py` & `evals/*.json` (`run.py`, `writing_benchmark_30.json`...)
* `skills/**/` (`reading_item_generation/`, `study_plan/`, `vocab_coach/`)
* `docs/` & `reports/`

**Tất cả các file trên hiện đang là file placeholder rỗng (0 bytes).**
* **Lý do:** Khóa trước cấu trúc thư mục và quy ước đường dẫn import (ví dụ: `from agent.tools.compute_tool import ...`) để tránh việc mỗi người tạo một thư mục khác nhau gây gãy toàn bộ import khi ghép nối.
* **Quy tắc tuyệt đối:**
  1. **KHÔNG tự ý xóa, đổi tên hoặc di chuyển** các file placeholder này.
  2. Mỗi thành viên chỉ chỉnh sửa và viết code vào **đúng các file thuộc phân công của mình** (xem bảng phân chia bên dưới).

---

## 2. Bảng phân quyền sở hữu File & Nhiệm vụ

| Thành viên | Phụ trách chính | Các file/thư mục thuộc quyền chỉnh sửa |
| :--- | :--- | :--- |
| **Thành viên 1** | Core Loop, LangGraph State, Loop Detector (UC-02) | `agent/core/state.py`<br>`agent/core/loop.py`<br>`agent/core/detector.py` |
| **Thành viên 2** | Tool Engineering, RAG Retriever, Practice Generator (UC-04) | `agent/tools/compute_tool.py`<br>`agent/tools/rag_tool.py`<br>`agent/tools/plagiarism_tool.py`<br>`agent/tools/vocab_tool.py`<br>`agent/tools/complexity_tool.py`<br>`skills/reading_item_generation/` |
| **Thành viên 3** | Skill Checks, Writing Assessment, Committee Workflow (UC-07) | `skills/writing_assessment/` (Đã hoàn thiện)<br>`agent/core/committee.py` (Đã hoàn thiện)<br>`tests/test_checks.py` (Đã hoàn thiện) |
| **Thành viên 4** | LangSmith Tracing, Benchmark, Eval Runner (UC-08) | `evals/`<br>`docs/data_sources.md`<br>`traces/` |
| **Thành viên 5** | FastAPI Backend, Web UI, Memory, HITL (UC-05, UC-10) | `backend/`<br>`frontend/`<br>`agent/tools/memory_tool.py`<br>`skills/study_plan/`<br>`reports/learner_reports/`<br>`docs/architecture.md` |

---

## 3. Quy trình làm việc & Thao tác Git an toàn

### Bước 1: Kéo code mới nhất từ `main` về máy
```bash
git checkout main
git pull origin main
```

### Bước 2: Cài đặt môi trường ảo và dependencies
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Cài đặt thư viện theo chuẩn
pip install -r requirements.txt
```

### Bước 3: Tạo nhánh tính năng riêng biệt
**Quy tắc:** Không bao giờ commit code trực tiếp lên `main`!
```bash
# Cú pháp: feature/m<so_thanh_vien>-<ten_chuc_nang>
# Ví dụ:
git checkout -b feature/m1-langgraph-state
git checkout -b feature/m2-rag-tools
```

### Bước 4: Mở file placeholder của mình và code
* Khi bắt đầu viết mã, hãy mở file placeholder tương ứng và thêm code vào.
* Chạy kiểm tra cú pháp và test trước khi commit:
  ```bash
  ruff check .
  pytest
  ```

### Bước 5: Đẩy nhánh lên GitHub và tạo Pull Request (PR)
```bash
git add .
git commit -m "feat(tools): implement count_words and rag_tool retriever"
git push origin feature/m2-rag-tools
```
* Vào GitHub tạo Pull Request trỏ vào nhánh `main`.
* GitHub Actions CI sẽ tự động kiểm tra xem code của bạn có làm hỏng test hoặc vi phạm ruff lint hay không.

---

## 4. Cách xử lý nếu gặp Merge Conflict trên File Placeholder

Nếu trong quá trình pull/merge bạn gặp thông báo conflict trên một file placeholder:
1. Mở file bị conflict.
2. Nếu bạn **không** phụ trách file đó, hãy chọn phiên bản của thành viên phụ trách (incoming changes).
3. Nếu đó là file của bạn và bạn đang viết code, giữ lại nội dung code của bạn.
4. Chạy `git add <tên_file>` và hoàn thành merge.
