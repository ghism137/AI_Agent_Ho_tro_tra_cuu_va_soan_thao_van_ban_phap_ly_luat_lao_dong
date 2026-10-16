# Legal form dataset — gói bàn giao

Gói hiện hành gồm **[v1](v1/README.md) + [v1.1](v1.1/README.md)**. Gửi cả hai folder cho đồng nghiệp: v1 chứa text chunks gốc; v1.1 bổ sung metadata và candidate/grouping index. Không có raw DOCX hoặc embedding trong gói này.

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
