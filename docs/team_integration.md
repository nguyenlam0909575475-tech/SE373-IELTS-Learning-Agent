# Nối Person 3 với code nhóm

Đối chiếu ngày 24/10/2026 với SE373-IELTS-Learning-Agent-main.zip. ZIP được đọc trực tiếp; chỉ các skill files cần dùng đã được sao chép vào workspace.

## Đã nối trong Person 3

- src/agent/team_adapters.py cung cấp build_team_dependencies(...), TeamRetriever, TeamTools, TeamSecurity, TeamValidators và MappingTaskBank. Adapter nối retriever của N2 và tools/validators/security của N4 vào Dependencies của graph.
- Adapter chuẩn hóa tên criterion cũ của validator N4 (coherence_and_cohesion, grammatical_range_and_accuracy) về enum public hiện hành (coherence_cohesion, grammatical_range_accuracy). JSON public vẫn theo WritingAssessment.
- N4 hiện tự làm tròn điểm Task đến 0.5. Quyết định Person 3 trong docs/open_decisions.md giữ trung bình số học chưa làm tròn. Adapter kiểm tra overall_band public bằng raw mean, rồi chỉ đưa một bản xem nội bộ đã làm tròn cho validator cũ kiểm tra các cờ và tín hiệu khác.
- Skill skills/writing-assessment và schema JSON được thêm vào repo. scripts/sync_writing_schema.py sinh/kiểm tra schema trực tiếp từ model; prompt thật nạp instructions.md; trace ghi skill_name/skill_version.
- Graph gọi src.skill_checks.run_checks làm entrypoint skill. Lỗi validator tiếp tục là ValidationIssue riêng, không nhập vào assessment.flags.

## Ví dụ composition root

    from src.agent.graph import build_graph
    from src.agent.team_adapters import MappingTaskBank, build_team_dependencies

    bank = MappingTaskBank({
        "BANK_T2_001": {
            "item_id": "BANK_T2_001",
            "task_type": "task2",
            "task_prompt": "Đề tự soạn đã được duyệt.",
            "source": "self_written",
            "license": "CC0-1.0",
        }
    })
    deps = build_team_dependencies(task_bank=bank, examiner=examiner)
    graph = build_graph(dependencies=deps)
    result = graph.invoke({"request": {
        "item_id": "BANK_T2_001",
        "task_type": "task2",
        "essay": "Bài viết của người học...",
    }})

Trong ví dụ thật, không dùng nội dung placeholder trên. Nguồn đề, giấy phép và material Task 1 phải được N1/N5 cung cấp. examiner được khởi tạo tường minh trong composition root; nạp module/adapter không tự gọi API.

## Việc còn chặn tích hợp end-to-end

- ZIP để data/bank/writing_task1.json và writing_task2.json rỗng. N5/N1 chưa bàn giao bank có item_id, nguồn, giấy phép và material Task 1. MappingTaskBank là điểm cắm, chưa phải dữ liệu bank thật.
- Chroma DB chưa có trong ZIP; N2 yêu cầu tái tạo local từ descriptor pipeline trước khi retrieval chạy.
- Corpus mẫu có hai đoạn có metadata nguồn/giấy phép, nhưng chưa được đánh giá khả năng phát hiện đạo văn và quyền áp dụng của từng văn bản cho mục đích này. Adapter dừng khi tool không chạy được; không biến lỗi thành “không đạo văn”.
- Frontend hiện trong ZIP chỉ ánh xạ nhãn cũ coherence_and_cohesion/grammatical_range_and_accuracy; N5 cần thêm alias hiển thị cho hai enum public của Person 3. Frontend cũng dùng String.slice trực tiếp với offset codepoint Python; cần đổi offset sang UTF-16 trước khi highlight emoji/non-BMP. Backend hiện gửi prompt trực tiếp và response kiểu cũ, trong khi graph nhận item_id/task_type/essay và trả AgentSuccess/AgentError kèm run_id; N5 cần viết lớp API mapping khi nối graph.
- N2 cung cấp Band 0 policy qua get_band_zero_policy() riêng. Output Person 3 hiện bắt evidence/ref cho đủ bốn tiêu chí; chưa có thống nhất contract để biểu diễn policy Band 0 không có chunk_id, nên adapter chưa tự gán Band 0.
- Adapter dự kiến dùng trong repo hợp nhất, nơi các module N2/N4 nằm đúng package như trong ZIP (src.tools, agent.tools, skills.writing_assessment). ZIP chưa được chép đè lên repo Person 3.

## Kiểm chứng

python -m scripts.sync_writing_schema --module src.agent.schemas --check xác nhận schema trong skill đồng bộ với Pydantic. python -m pytest -q và python -m examples.run_offline_demo chạy được trên harness offline. Các lần này xác nhận Person 3 vẫn hoạt động; chưa phải end-to-end với Chroma, N4 production tools, bank thật hay corpus chuẩn.
