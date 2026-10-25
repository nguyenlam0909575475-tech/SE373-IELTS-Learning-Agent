# BÁO CÁO KẾT QUẢ ĐÁNH GIÁ TỰ ĐỘNG PHASE 1 (EVALUATION REPORT)

* **Học phần:** SE373 - Agentic AI Systems Engineering
* **Use Case:** UC-02 — Automated IELTS Writing Assessment & Harness Verification
* **Chế độ thực thi:** `MOCK`
* **Thời gian chạy:** `2026-10-25T18:12:17Z`
* **Tổng số bài kiểm thử:** `48` (Benchmark: 30, Security: 12, Functional: 6)

---

## 1. Bảng Tổng Hợp Chỉ Số Kiểm Thử So Với Ngưỡng Nghiệp Vụ (UC-02)

| Chỉ số đánh giá | Giá trị đạt được | Ngưỡng yêu cầu UC-02 | Trạng thái |
| :--- | :---: | :---: | :---: |
| **Tỷ lệ Quote đúng nguyên văn 100%** | **100.0%** | 100.0% | ✅ ĐẠT |
| **Tỷ lệ Khớp tọa độ [start:end]** | **100.0%** | 100.0% | ✅ ĐẠT |
| **Tỷ lệ Descriptor Refs hợp lệ** | **100.0%** | 100.0% (Không rò rỉ Task khác) | ✅ ĐẠT |
| **Độ lệch Band <= 0.5** | **70.0%** | >= 60.0% | ✅ ĐẠT |
| **Độ lệch Band <= 1.0** | **93.3%** | >= 90.0% | ✅ ĐẠT |
| **Mean Absolute Error (MAE)** | **0.583** | Càng nhỏ càng tốt | ✅ ĐẠT |
| **Tỷ lệ bảo mật SecurityGuard** | **100.0%** | 100.0% (Bắt đúng injection, không phạt safe) | ✅ ĐẠT |
| **Cảnh báo độ dài (under_length)** | **100.0%** | 100.0% (< 150 cho Task 1, < 250 cho Task 2) | ✅ ĐẠT |
| **Phạt bài lạc đề (off_topic)** | **100.0%** | 100.0% (TR/TA cap <= 5.0) | ✅ ĐẠT |
| **Độ trễ xử lý trung bình** | **735.92 ms** | Yêu cầu thời gian thực | ✅ ĐẠT |

---

## 2. Kết Quả Chi Tiết Từng Bài Trên Tập Benchmark (30 Bài)

| ID | Task | Số từ | Điểm Chuẩn | AI Dự Đoán | Độ Lệch | Harness Passed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `bench_01` | task1 | 156 | 6.5 | 6.5 | 0.0 | ✅ |
| `bench_02` | task1 | 69 | 5.0 | 5.5 | 0.5 | ✅ |
| `bench_03` | task1 | 132 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_04` | task1 | 116 | 6.0 | 6.0 | 0.0 | ✅ |
| `bench_05` | task1 | 119 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_06` | task1 | 112 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_07` | task1 | 113 | 6.0 | 6.0 | 0.0 | ✅ |
| `bench_08` | task1 | 117 | 7.0 | 6.0 | 1.0 | ✅ |
| `bench_09` | task1 | 113 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_10` | task1 | 123 | 7.5 | 6.0 | 1.5 | ✅ |
| `bench_11` | task1 | 101 | 5.5 | 6.0 | 0.5 | ✅ |
| `bench_12` | task1 | 117 | 6.0 | 6.0 | 0.0 | ✅ |
| `bench_13` | task2 | 175 | 7.0 | 6.0 | 1.0 | ✅ |
| `bench_14` | task2 | 163 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_15` | task2 | 178 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_16` | task2 | 170 | 7.0 | 6.0 | 1.0 | ✅ |
| `bench_17` | task2 | 179 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_18` | task2 | 193 | 7.0 | 6.0 | 1.0 | ✅ |
| `bench_19` | task2 | 135 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_20` | task2 | 173 | 7.0 | 6.0 | 1.0 | ✅ |
| `bench_21` | task2 | 157 | 6.0 | 6.0 | 0.0 | ✅ |
| `bench_22` | task2 | 132 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_23` | task2 | 124 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_24` | task2 | 147 | 7.0 | 6.0 | 1.0 | ✅ |
| `bench_25` | task2 | 159 | 7.5 | 6.0 | 1.5 | ✅ |
| `bench_26` | task2 | 173 | 6.5 | 6.0 | 0.5 | ✅ |
| `bench_27` | task2 | 177 | 5.5 | 6.0 | 0.5 | ✅ |
| `bench_28` | task2 | 159 | 6.0 | 6.0 | 0.0 | ✅ |
| `bench_29` | task2 | 170 | 7.0 | 6.0 | 1.0 | ✅ |
| `bench_30` | task2 | 161 | 6.5 | 6.0 | 0.5 | ✅ |

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
