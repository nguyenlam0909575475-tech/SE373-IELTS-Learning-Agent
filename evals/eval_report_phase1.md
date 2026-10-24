# BÁO CÁO KẾT QUẢ ĐÁNH GIÁ TỰ ĐỘNG PHASE 1 (EVALUATION REPORT)

* **Học phần:** SE373 - Agentic AI Systems Engineering
* **Use Case:** UC-02 — Automated IELTS Writing Assessment & Harness Verification
* **Chế độ thực thi:** `MOCK`
* **Thời gian chạy:** `2026-10-24T05:09:27Z`
* **Tổng số bài kiểm thử:** `48` (Benchmark: 30, Security: 12, Functional: 6)

---

## 1. Bảng Tổng Hợp Chỉ Số Kiểm Thử So Với Ngưỡng Nghiệp Vụ (UC-02)

| Chỉ số đánh giá | Giá trị đạt được | Ngưỡng yêu cầu UC-02 | Trạng thái |
| :--- | :---: | :---: | :---: |
| **Tỷ lệ Quote đúng nguyên văn 100%** | **100.0%** | 100.0% | ✅ ĐẠT |
| **Tỷ lệ Khớp tọa độ [start:end]** | **100.0%** | 100.0% | ✅ ĐẠT |
| **Tỷ lệ Descriptor Refs hợp lệ** | **100.0%** | 100.0% (Không rò rỉ Task khác) | ✅ ĐẠT |
| **Độ lệch Band <= 0.5** | **96.7%** | >= 60.0% | ✅ ĐẠT |
| **Độ lệch Band <= 1.0** | **100.0%** | >= 90.0% | ✅ ĐẠT |
| **Mean Absolute Error (MAE)** | **0.25** | Càng nhỏ càng tốt | ✅ ĐẠT |
| **Tỷ lệ bảo mật SecurityGuard** | **100.0%** | 100.0% (Bắt đúng injection, không phạt safe) | ✅ ĐẠT |
| **Cảnh báo độ dài (under_length)** | **100.0%** | 100.0% (< 150 cho Task 1, < 250 cho Task 2) | ✅ ĐẠT |
| **Phạt bài lạc đề (off_topic)** | **100.0%** | 100.0% (TR/TA cap <= 5.0) | ✅ ĐẠT |
| **Độ trễ xử lý trung bình** | **0.79 ms** | Yêu cầu thời gian thực | ✅ ĐẠT |

---

## 2. Kết Quả Chi Tiết Từng Bài Trên Tập Benchmark (30 Bài)

| ID | Task | Số từ | Điểm Chuẩn | AI Dự Đoán | Độ Lệch | Harness Passed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `bench_01` | task1 | 176 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_02` | task2 | 264 | 7.0 | 6.5 | 0.5 | ✅ |
| `bench_03` | task1 | 56 | 5.0 | 5.0 | 0.0 | ✅ |
| `bench_04` | task2 | 279 | 6.5 | 7.0 | 0.5 | ✅ |
| `bench_05` | task2 | 267 | 6.0 | 6.5 | 0.5 | ✅ |
| `bench_06` | task1 | 172 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_07` | task2 | 286 | 7.0 | 7.0 | 0.0 | ✅ |
| `bench_08` | task1 | 177 | 6.0 | 6.5 | 0.5 | ✅ |
| `bench_09` | task2 | 268 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_10` | task2 | 282 | 7.0 | 7.0 | 0.0 | ✅ |
| `bench_11` | task1 | 170 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_12` | task2 | 278 | 6.5 | 7.0 | 0.5 | ✅ |
| `bench_13` | task1 | 161 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_14` | task2 | 260 | 7.0 | 6.5 | 0.5 | ✅ |
| `bench_15` | task2 | 279 | 6.5 | 7.0 | 0.5 | ✅ |
| `bench_16` | task1 | 164 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_17` | task2 | 263 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_18` | task1 | 179 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_19` | task2 | 282 | 6.5 | 7.0 | 0.5 | ✅ |
| `bench_20` | task1 | 174 | 6.0 | 7.0 | 1.0 | ✅ |
| `bench_21` | task2 | 264 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_22` | task1 | 165 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_23` | task2 | 264 | 7.0 | 6.5 | 0.5 | ✅ |
| `bench_24` | task1 | 161 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_25` | task2 | 261 | 7.0 | 6.5 | 0.5 | ✅ |
| `bench_26` | task1 | 174 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_27` | task2 | 275 | 6.5 | 7.0 | 0.5 | ✅ |
| `bench_28` | task1 | 166 | 6.0 | 6.5 | 0.5 | ✅ |
| `bench_29` | task2 | 267 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_30` | task2 | 263 | 7.0 | 6.5 | 0.5 | ✅ |

---

## 3. Kết Quả Kiểm Thử Bộ Bảo Mật Member 4 (SecurityGuard Cases)

| ID | Vị trí kiểm tra | Kết quả phát hiện | Kết quả mong đợi | Đánh giá |
| :--- | :---: | :---: | :---: | :---: |
| `N4-INJ-01` | essay | 🚨 Bắt Injection | 🚨 Bắt Injection | ✅ Thành công |
| `N4-INJ-02` | essay | 🚨 Bắt Injection | 🚨 Bắt Injection | ✅ Thành công |
| `N4-INJ-03` | essay | 🚨 Bắt Injection | 🚨 Bắt Injection | ✅ Thành công |
| `N4-INJ-04` | chunk | 🚨 Bắt Injection | 🚨 Bắt Injection | ✅ Thành công |
| `N4-INJ-05` | task | 🚨 Bắt Injection | 🚨 Bắt Injection | ✅ Thành công |
| `N4-INJ-06` | essay | 🚨 Bắt Injection | 🚨 Bắt Injection | ✅ Thành công |
| `N4-INJ-07` | essay | 🚨 Bắt Injection | 🚨 Bắt Injection | ✅ Thành công |
| `N4-INJ-08` | essay | 🚨 Bắt Injection | 🚨 Bắt Injection | ✅ Thành công |
| `N4-SAFE-01` | essay | 🟢 Safe | 🟢 Safe | ✅ Thành công |
| `N4-SAFE-02` | essay | 🟢 Safe | 🟢 Safe | ✅ Thành công |
| `N4-SAFE-03` | essay | 🟢 Safe | 🟢 Safe | ✅ Thành công |
| `N4-SAFE-04` | chunk | 🟢 Safe | 🟢 Safe | ✅ Thành công |

---

## 4. Kết Luận & Hướng Tiếp Tục

* Bộ công cụ tất định của Người 4 (`compute_tool`, `security_tool`, `plagiarism_tool`) đã được tích hợp hoàn toàn vào quy trình đánh giá tự động.
* Toàn bộ 12 ca kiểm thử bảo mật của Người 4 đều được SecurityGuard nhận diện chính xác 100%.
* Hệ thống Harness verification của Phase 1 đạt 100% tiêu chí chấp nhận cho việc kiểm soát trích dẫn dẫn chứng nguyên văn và tọa độ ký tự.
