# Hướng dẫn agent cho repo

- Đọc `.claude/CLAUDE.local.md` và phần trạng thái hiện hành trong `.claude/project/session_state.md` trước khi làm việc.
- Phase 1 đang ACTIVE (đã unpause); Phase 2 chỉ DESIGN_ONLY theo yêu cầu 2026-09-18. Không tự triển khai vì task cards đã tồn tại. Chỉ dẫn mới của người dùng có thể mở lại phạm vi.
- Dùng `.claude/project/project_guide.md` để phân model, task, tests và handoff; `.claude/project/phase2_design.md` là contract/gate Phase 2 hiện hành.
- Chỉ đọc plan/task được giao và inputs liên quan. Không quét raw corpus, venv, mọi reports/handoff để lấy context mặc định.
- Giữ thay đổi có sẵn. Không tự spawn subagents; vai trò trong plan là hướng dẫn giao việc sau này.
- Sửa docs chỉ kiểm docs; không chạy ingestion/embedding/full eval. Builder không tự cấp reviewer sign-off.
