# AI Agent Luật Lao Động — Bootstrap

Cập nhật 2026-09-23: review và lập kế hoạch hoàn tất Phase 1; Phase 2 chỉ thiết kế.

## Trạng thái hiện hành

- **Phase 1: ACTIVE/OPEN, closeout chưa nghiệm thu.** Đã review repair ngày 23/09; dùng [completion plan](project/phase1_completion_plan_2026-09-23.md). Builder Sol/Terra chỉ thực thi task được giao; active release không chứng minh acceptance.
- **Phase 2: DESIGN_ONLY.** Đã lập thiết kế v2 và task cards; chưa cài đặt, code, tạo fixtures, embed, index hoặc eval. Không tự bắt đầu task vì có kế hoạch.
- Phase 3–7: giữ roadmap hiện có, không mở thiết kế/thực thi trong yêu cầu này.

## Đọc theo nhu cầu

1. [Trạng thái hiện hành](project/session_state.md), chỉ phần đầu; các mục lịch sử không cấp quyền chạy tiếp.
2. [Project Guide](project/project_guide.md): routing model, giới hạn scope, prompt/handoff và kiểm tra đúng mức.
3. [Phase 2 design](project/phase2_design.md) + duy nhất task card được giao; không nạp mọi plan/agent prompt.
4. Phase 1: [completion plan 23/09](project/phase1_completion_plan_2026-09-23.md), findings và duy nhất task được giao. Handoff paused 18/09 là lịch sử, không còn là trạng thái hiện hành.

## Nguyên tắc

- Runtime sản phẩm budget $0; tài nguyên và quota phải kiểm thực tế. Không mặc định thời gian/token phát triển vô hạn.
- Tính toán bằng Python deterministic; trích dẫn có nguồn/locator và version phù hợp ngày áp dụng; thiếu evidence không đoán.
- Một task, một owner, allowlist file rõ; không tự spawn hoặc chạy song song vì sơ đồ có nhiều vai trò.
- Model mapping có một nguồn tại Project Guide; ghi actual model/effort, không giả nhận đã dùng model khác.
- Giữ thay đổi có sẵn của người dùng. Sign-off cần reviewer/evidence thật trên cùng digest; builder done không phải acceptance.

## Bản đồ

- [Operations Guide](project/operations_guide.md): roadmap và điều phối.
- [Technical Design](project/technical_design.md): kiến trúc tổng thể; snippets cũ là định hướng, phase contract mới hơn quyết định triển khai.
- [Project spec](project/Project.md), [issues](project/open_issues.md).
- Rules: [workflow](rules/workflow.md), [tech defaults](rules/tech_defaults.md), [core principles](rules/core_principles.md), [response format](rules/response_format.md).
- Vai trò khi cần: `agents/rag-engineer-agent.md`, `agents/eval-qa-agent.md`, `agents/reviewer-agent.md`; không bắt mọi phiên đọc tất cả.

## Kết thúc phiên

Coordinator cập nhật phần trạng thái hiện hành trong session_state. Khi thực thi task sau này, builder chỉ ghi packet task theo guide; không chép lại lịch sử dài, không tự commit toàn working tree hoặc tuyên bố gate PASS từ một test.
