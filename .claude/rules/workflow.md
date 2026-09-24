# Workflow — task nhỏ, bằng chứng rõ

## Phạm vi hiện hành

- Phase 1 ACTIVE/OPEN; dùng completion plan 23/09 và task được giao. Phase 2 DESIGN_ONLY cho đến khi người dùng giao triển khai.
- Chỉ sửa docs khi được yêu cầu design; không chạy code/fixtures/embedding/index/eval trước.
- Routing/model/prompt/handoff dùng `.claude/project/project_guide.md`, không sao chép mapping sang nhiều file.

## Đầu phiên

1. Đọc bootstrap, trạng thái hiện hành và task card; đọc thêm đúng input allowlist.
2. Xác định owner, dependency, outputs, tests, stop condition trước khi sửa.
3. Kiểm working tree; giữ nguyên thay đổi ngoài scope. Không tự commit/reset/stash toàn repo.

## Trong phiên

- Một task, một writer/file. Vai trò trong plan không tự cho phép spawn hay song song.
- Contract đổi cần quyết định hẹp của designer; thiếu data chuyển upstream issue, không tự mở rộng ngoài task Phase 1 được giao.
- Hai vòng cùng lỗi không tiến triển: ghi reproduction và blocker, tách/chuyển task đúng vai trò.
- Không thay metadata/evidence để vượt gate. Không đổi snapshot giữa một lần chạy.

## Kiểm tra theo thay đổi

- Docs: links, task dependencies, consistency; không chạy pytest/full eval.
- Code retrieval: targeted tests; checkpoint chạy retrieval integration suite.
- Full corpus eval chỉ ở P2-10 sau accepted release + frozen gold/config.
- Calculation khi được giao sau này: toàn bộ calculation unit tests và căn cứ nguồn.
- Không chạy lại kiểm tra đã đạt nếu không có diff/input/config mới hoặc vấn đề chưa giải.

## Handoff

- Packet riêng mỗi task: actual model, input/diff hashes, outputs, commands/exit codes, tests, unresolved issues.
- Builder done và reviewer sign-off tách biệt; review gộp theo checkpoint, không review mọi edit.
- Reviewer chỉ xác nhận scope/digest đã kiểm; ghi NOT_RUN cho kiểm tra chưa chạy.
- Coordinator cập nhật session_state hiện hành; lịch sử append-only không phải trạng thái hiện tại.
- Commit/PR khi thuộc phạm vi được giao; branch mới mặc định `codex/` hoặc tên người dùng yêu cầu.
