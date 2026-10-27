# KẾ HOẠCH TRIỂN KHAI (IMPLEMENTATION.MD)
## Loại bỏ hoàn toàn Mock Agent & Chuyển sang 100% Live Agent Core (Thành viên 3)

> **Mục tiêu:** Xóa bỏ toàn bộ bộ giả lập Offline Mock (`DeterministicAgentExaminer`), loại bỏ cơ chế công tắc Mock/Live chuyển sang mặc định 100% Agentic AI của Thành viên 3 (LangGraph StateGraph + Real LLM + Verification Harness), tối ưu hóa hiển thị `#resultsView` để phản ánh đúng năng lực của Agent.
> **Ràng buộc:** Tuân thủ nghiêm ngặt quy định **FREEZE** trong `AGENTS.md` (Giữ nguyên cấu trúc `#homeView`, `.cd-header`, `.app-footer`, `#reviewScreenView`).

---

## 1. Danh sách các thành phần cần XÓA / LOẠI BỎ (Clean-up Scope)

### 1.1. Trong `backend/live_service.py`
- [x] **Xóa toàn bộ class `DeterministicAgentExaminer` (~420 dòng code):**
  - Xóa bảng điểm hardcode theo độ dài (`w_count < 250 -> TR 5.5, CC 6.0, LR 6.0, GRA 5.5`).
  - Xóa toàn bộ các câu nhận xét tiếng Việt mẫu được gán sẵn (`comments_map`).
  - Xóa heuristic `_detect_off_topic_heuristic` dùng regex tìm từ khóa thô sơ.
  - Xóa mảng luật sửa lỗi regex `REWRITE_RULES` và logic cắt ghép câu kết bài tạo ra lỗi `"In summary, i believe..."`.
- [x] **Xóa cơ chế Fallback âm thầm sang Mock trong hàm `_get_examiner`:**
  - Hiện tại nếu LLM lỗi hoặc không có cấu hình, code `except Exception: pass` rồi âm thầm trả về `DeterministicAgentExaminer`.
  - Thay thế bằng logic: Khởi tạo trực tiếp `GeminiExaminer` hoặc `OpenAICompatibleExaminer`. Nếu cấu hình thiếu hoặc sai API key, trả về lỗi rõ ràng (`RuntimeError / DependencyFailure`) có mã lỗi có cấu trúc, tuyệt đối không âm thầm sinh kết quả giả.
- [x] **Xóa tham số `use_mock: bool = False`:**
  - Bỏ toàn bộ cờ `use_mock` trong `run_live_assessment` và `_get_examiner`.

### 1.2. Trong `backend/config.py`
- [x] **Xóa bỏ cờ `USE_MOCK_AGENT`:**
  - Loại bỏ `USE_MOCK_AGENT = os.getenv(...)`.
  - Xóa các hàm helper `get_mock_mode()` và `set_mock_mode()`.
- [x] **Chuẩn hóa cấu hình LLM cho OpenAI / Gemini:**
  - Đảm bảo đọc đúng các biến: `OPENAI_API_KEY`, `OPENAI_BASE_URL` (mặc định đúng endpoint official `https://api.openai.com/v1`), `OPENAI_MODEL` (ví dụ `gpt-4o-mini`).
  - Hỗ trợ `GEMINI_API_KEY`, `GEMINI_MODEL` (ví dụ `gemini-1.5-flash` hoặc `gemini-2.0-flash`).

### 1.3. Trong `backend/main.py`
- [x] **Loại bỏ endpoint và trường Mock:**
  - Xóa trường `mock: bool | None` trong schema `AssessmentRequest`.
  - Xóa endpoint `POST /api/config/toggle-mock`.
  - Đặt `execution_mode = "agent"` cố định trong `AssessmentResponse`.
  - Cập nhật endpoint `/api/assess-writing` gọi trực tiếp `run_agent_assessment` của tv3 mà không truyền cờ mock.

### 1.4. Trong `frontend/app.js`
- [x] **Loại bỏ logic Mock:**
  - Xóa bỏ việc gửi cờ `mock` trong payload lên API `/api/assess-writing`.
  - Cập nhật hiển thị nhãn `resExecMode` thành `"AGENT (LIVE)"`.
- [x] **Cải tiến hiển thị `#resultsView`:**
  - Ẩn các mã định danh thô của RAG (ví dụ `#writing_task2_task_response_b6_2023_05`). Thay bằng badge hiển thị chuẩn: `Barem: Task 2 - Band 6.0`.
  - Hiển thị trích dẫn dẫn chứng (`evidence quotes`) trực quan ngay trong thẻ tiêu chí để người học thấy rõ câu văn nào là cơ sở chấm điểm.
  - Hiển thị gợi ý sửa lỗi thực thụ từ Agent (nếu bài không có lỗi, hiển thị thông báo tích cực "Không phát hiện lỗi diễn đạt đáng kể", không bịa lỗi).

---

## 2. Kiến trúc tích hợp trực tiếp 100% Agent của Thành viên 3

Toàn bộ quá trình chấm bài sẽ đi qua đúng quy trình chuẩn của LangGraph StateGraph do tv3 xây dựng trong `src/agent/`:

```
               [Học viên nộp bài từ Frontend]
                             │
                             ▼
               [FastAPI: POST /api/assess-writing]
                             │
                             ▼
          [backend/live_service.py: run_agent_assessment]
                             │
       ┌─────────────────────┴──────────────────────┐
       │     LangGraph StateGraph (tv3 Core Loop)   │
       │                                            │
       │  1. resolve_task (Task Bank N1)            │
       │  2. prepare_tools (count_words N4)         │
       │  3. retrieve_rubric (RAG Descriptors N2)   │
       │  4. examiner (Gemini / OpenAI Examiner)    │
       │     └─ Prompt LLM với System Instruction  │
       │     └─ Sinh Structured JSON Draft          │
       │  5. verify (Verification Node)             │
       │     ├─ compute_band (Python tất định N4)  │
       │     ├─ quote_validator (so khớp nguyên văn)│
       │     └─ Self-Correction Retry (tối đa 2 lần)│
       │  6. finalize (Trả về WritingAssessment)    │
       └─────────────────────┬──────────────────────┘
                             │
                             ▼
          [Frontend #resultsView: Hiển thị kết quả thật]
```

---

## 3. Các bước triển khai chi tiết (Action Plan)

### Bước 1: Dọn sạch Mock trong `backend/live_service.py`
1. Xóa class `DeterministicAgentExaminer` và hàm `_detect_off_topic_heuristic`.
2. Sửa hàm `_get_examiner()`:
   - Đọc cài đặt OpenAI/Groq từ `load_openai_settings()`. Nếu hợp lệ và API key có thật, trả về `OpenAICompatibleExaminer`.
   - Đọc cài đặt Gemini từ `load_gemini_settings()`. Nếu hợp lệ và API key có thật, trả về `GeminiExaminer`.
   - Nếu không có bất kỳ cấu hình hợp lệ nào, ném ra ngoại lệ `RuntimeError("Yêu cầu cấu hình OPENAI_API_KEY hoặc GEMINI_API_KEY trong file .env để chạy Live Agent.")`.
3. Sửa hàm `run_live_assessment()`: Bỏ tham số `use_mock`.

### Bước 2: Cập nhật `backend/config.py` và `backend/main.py`
1. Trong `backend/config.py`: Xóa `USE_MOCK_AGENT`, `get_mock_mode()`, `set_mock_mode()`.
2. Trong `backend/main.py`:
   - Làm sạch `AssessmentRequest` (không còn trường `mock`).
   - Xóa `ToggleMockRequest` và endpoint `/api/config/toggle-mock`.
   - Cập nhật `/api/config` và `/api/health`.
   - Cập nhật `/api/assess-writing` chỉ chạy chế độ Agent.

### Bước 3: Tối ưu hóa cấu hình `.env` cho LLM thật
1. Đảm bảo cấu hình OpenAI chuẩn xác:
   - `OPENAI_API_KEY=<key_cua_ban>`
   - `OPENAI_BASE_URL=https://api.openai.com/v1`
   - `OPENAI_MODEL=gpt-4o-mini`
   - `OPENAI_RESPONSE_FORMAT=json_object`
2. Hoặc cấu hình Gemini chuẩn xác:
   - `GEMINI_API_KEY=<key_cua_ban>`
   - `GEMINI_MODEL=gemini-1.5-flash`

### Bước 4: Tinh chỉnh Giao diện `#resultsView` trong `frontend/app.js`
1. Đảm bảo không vi phạm các thành phần **FREEZE** (`#homeView`, `.cd-header`, `.app-footer`, `#reviewScreenView`).
2. Trong hàm `renderAssessmentResults`:
   - Ghi nhận `resExecMode` là `AGENT (LIVE)`.
   - Cập nhật `renderCriteriaCards`:
     + Không hiển thị ID thô dạng hashtag `#writing_task2_...`. Thay thế bằng nhãn chuẩn hóa: ví dụ `Barem Task 2 - Band 6.0`.
     + Đưa câu trích dẫn dẫn chứng (`crit.evidence[0].quote`) vào trực tiếp trong thẻ tiêu chí dưới dạng khối blockquote dẫn chứng rõ ràng.
3. Trong hàm `renderCorrections`:
   - Nếu `corrections` có dữ liệu: Hiển thị thẻ sửa lỗi với giải thích ngữ pháp từ LLM.
   - Nếu `corrections` rỗng: Hiển thị badge xanh: *"Bài viết duy trì câu văn tự nhiên, không phát hiện lỗi diễn đạt cần chỉnh sửa"*.

### Bước 5: Kiểm thử xác nhận (Verification)
1. Chạy `pytest` toàn bộ test suite để đảm bảo không gãy các kiểm thử tích hợp của tv3, tv4, tv2.
2. Khởi chạy server FastAPI và submit thử đề Task 2 mẫu:
   - Xác nhận log hiển thị: `Using OpenAI-compatible live examiner` hoặc `Using Gemini live examiner`.
   - Xác nhận không còn một dòng log nào liên quan đến `DeterministicAgentExaminer`.
   - Xác nhận điểm số, nhận xét và dẫn chứng được sinh 100% từ mô hình ngôn ngữ lớn thật thông qua LangGraph.

---

## 4. Bảng kiểm tra tuân thủ Freeze Rules

| Thành phần | Trạng thái | Đảm bảo thực hiện |
| :--- | :---: | :--- |
| **Giao diện Trang chủ (`#homeView`)** | ❄️ **FREEZE** | Giữ nguyên 100% cấu trúc HTML và CSS |
| **Header & Footer (`.cd-header`, `.app-footer`)**| ❄️ **FREEZE** | Giữ nguyên 100% cấu trúc HTML (timer, nút nộp bài, footer) |
| **Màn hình Xem lại bài làm (`#reviewScreenView`)**| ❄️ **FREEZE** | Giữ nguyên 100% cấu trúc modal xem lại 2 Part và nút xác nhận |
| **Màn hình Kết quả (`#resultsView`)** | 🛠 **Được phép tinh chỉnh** | Giữ nguyên layout container, chỉ tối ưu cách render thẻ tiêu chí & dẫn chứng |
