# Legal form dataset — gói bàn giao

Gói hiện hành gồm **[v1](v1/README.md) + [v1.1](v1.1/README.md)**. Gửi cả hai folder cho đồng nghiệp: v1 chứa text chunks gốc; v1.1 bổ sung metadata và candidate/grouping index. Không có raw DOCX hoặc embedding trong gói này.

## Tích hợp vào branch dữ liệu frozen — 16/10/2026

Gói export được bổ sung vào `codex/frozen-demo-data-20261009` theo yêu cầu owner, trên baseline frozen `5ae5c56fdc26dec07dc32daaaa694080a6f51011`. Chỉ tích hợp bốn commit của task từ main bằng cherry-pick: `9bf662b` → `8f9d295`, `4611111` → `609aa96`, `f6e9023` → `e4deee7`, `897449c` → `99c76cf`. Các thay đổi Phase 1 khác của main không được đưa sang branch này.

Toàn bộ `demo-data/`, gồm preview ngày 29/09 và SOURCE_ONLY manifest/supplement ngày 09/10, giữ nguyên Git tree và hashes của baseline frozen. Gói `exports/legal_forms/` sử dụng published release `phase1-febf5129f0e33d40`; đây là dữ liệu bổ sung riêng, không thay corpus SOURCE_ONLY hoặc thay đổi search baseline 9.520 chunks. Nội dung các folder v1/v1.1, tooling và báo cáo review khớp bytes từ main `897449cc797c0c872186ed0fd2e2447aaec669e0`.

Commit được reviewer nghiệm thu vẫn là `f6e9023` trên dòng main; commit cherry-pick tương ứng có cùng nội dung sửa. Để tái lập trong một clone chỉ tải branch frozen, cần tải các pinned source commits từ main (`git fetch origin main`) và cung cấp riêng source repository có published release/raw files được pin bằng hash. Các nguyên liệu đó không được copy vào gói export.

## Nội dung

- **v1**: 212 form chunks, 131 annex chunks; 15 văn bản có form và tổng 21 văn bản khi tính annex. Xem [danh sách văn bản](v1/README.md#những-văn-bản-đã-có-biểu-mẫu-được-chunk) và [catalog 185 logical form provisions](v1/FORM_CATALOG.md). Số provision không phải số biểu mẫu pháp lý đã deduplicate.
- **v1.1**: 343 metadata overlay rows; 208 candidate groups (185 form + 23 annex candidates); 257 nhóm chunk theo provision/version; queue riêng cho 23 annex NEEDS_REVIEW; metadata/helper dedup bảo toàn nguồn và phiên bản.
- Mỗi phiên bản có manifest và SHA256SUMS. V1 và sáu file dữ liệu dẫn xuất v1.1 giữ nguyên bytes của commit đã review; README/manifest/checksums được cập nhật để phản ánh nghiệm thu.

## Nghiệm thu engineering

**MANUAL_ENGINEERING_REVIEW = ACCEPT; EXP11-R01 = CLOSED** trên commit `f6e9023e70e282998e13bfb4d73608ad4e0e221d`, ngày 16/10/2026. Reviewer độc lập chạy lại **37/37 tests PASS**, xác nhận provenance thiếu/rỗng/sai kiểu bị từ chối và không có finding P1/P2 mới trong scope.

[Báo cáo re-review ACCEPT](reviews/EXPORT_PHASE1_V11_REREVIEW_f6e9023_20261016.md) · [Báo cáo MODIFY trước sửa](reviews/EXPORT_PHASE1_V11_REVIEW_4611111_20261016.md) · [Packet và lịch sử xử lý](V1.1_REVIEW_REQUEST.md).

Đây là review trực tiếp, **không phải Bugbot**. Owner đã cho phép cập nhật README và đưa gói lên GitHub main. Commit tracking sau review chỉ ghi nhận quyết định và cập nhật tài liệu/metadata; không mở rộng scope nghiệm thu của commit đã review.

## Các giới hạn vẫn còn

- `LEGAL_APPLICABILITY_UNVERIFIED`: ngày hiệu lực/issued date đáng ngờ và sự khác biệt source `pending` / chunk `verified` còn cần review pháp lý. Không tự sửa metadata gốc.
- `STRUCTURAL_FIDELITY_LIMITATION`: bảng và layout chỉ có text; không nghiệm thu DOCX render, ô gộp hoặc khôi phục lossless.
- Candidate index không chứng minh chọn đúng mẫu theo yêu cầu ngữ nghĩa. Annex candidates và DOCX alternatives vẫn cần đối chiếu nguồn.
- Overlay giữ `PENDING_REVIEW`, `TEXT_ONLY`, `generation_ready=false`. Automated legal document generation production vẫn **BLOCKED**.

Published Phase 1 release và active pointer giữ nguyên. Gói này không mở lại crawl, ingestion, embedding/index hoặc toàn bộ Phase 1 closeout.
