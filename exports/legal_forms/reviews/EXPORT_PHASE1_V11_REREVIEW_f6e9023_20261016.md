# Export Phase 1 v1.1 — EXP11-R01 re-review

Ngày 16/10/2026, Asia/Saigon. Reviewer trực tiếp: Codex trong conversation review Export Phase 1 này, không phải runner Bugbot. Reviewer không sửa implementation hoặc generated package.

## Quyết định

- Exact reviewed commit: f6e9023e70e282998e13bfb4d73608ad4e0e221d.
- Branch: codex/phase1-legal-form-export.
- Worktree: C:/Users/Admin/.codex/visualizations/2026/10/16/01a1443e-cb2f-7541-ad6a-3c963e92a92d/legal-form-export.
- Repair delta so với review trước: 4611111680835bf8eb8264a7afe6369aa7fb9ff6 → f6e9023e70e282998e13bfb4d73608ad4e0e221d, 6 files.
- EXP11-R01 = CLOSED.
- MANUAL_ENGINEERING_REVIEW = ACCEPT cho engineering export v1.1 trong scope đã review trước cùng repair delta này.
- Không phát hiện finding P1/P2 mới trong diff và invariants đã kiểm.
- Working tree CLEAN trước và sau tests; không commit, merge hoặc push.

Báo cáo này nối tiếp [review gốc](EXPORT_PHASE1_V11_REVIEW_4611111_20261016.md), giữ nguyên báo cáo MODIFY của commit cũ; không sửa lịch sử hoặc tự coi builder observations là kết quả review.

## Căn cứ đóng EXP11-R01

Đã đọc trực tiếp guard mới tại [build_legal_forms_v11.py:36](C:/Users/Admin/.codex/visualizations/2026/10/16/01a1443e-cb2f-7541-ad6a-3c963e92a92d/legal-form-export/scripts/build_legal_forms_v11.py:36): source_refs phải là list khác rỗng, từng phần tử là object, mọi source_id và locator đều là string khác rỗng sau kiểm whitespace. Kiểm tra tất cả references trước canonicalization/grouping. Không normalize hoặc mutate giá trị nguồn; source_url null vẫn hợp lệ khi ID/locator đầy đủ.

Các negative tests mới phủ missing/null/blank/whitespace/NBSP/wrong type, malformed containers và reference hỏng nằm trước/sau một reference đúng. Positive test giữ same-context collapse và không mutate input; các test cross-source/version/locator trước đó vẫn đạt. Không mở rộng equality semantics của is_fragment ngoài repair được yêu cầu.

Đã chạy thêm probe độc lập ngoài bộ tests builder, trên bản sao bộ nhớ của một exported record: `[{}]`, reference thiếu locator, ID/locator rỗng, source_id=False, locator=[] và locator=NBSP. Cả 6/6 trường hợp bị ValueError, không bị collapse và không làm đổi input. Đây bao gồm đúng trigger đã báo ở commit cũ.

## Kiểm thử và integrity

Lệnh từ exact feature checkout:

```powershell
$env:LEGAL_FORM_SOURCE_REPO='C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động'
python -X utf8 -m unittest discover -s tests -p 'test_legal_form*.py' -v
git diff --check 4611111680835bf8eb8264a7afe6369aa7fb9ff6..f6e9023e70e282998e13bfb4d73608ad4e0e221d
```

Kết quả độc lập: 37/37 PASS, 0 failures, 0 skips, 10.452 giây, exit 0, Python 3.14.2 stdlib. Suite gồm F09 missing-raw fail-before-output, snapshot/raw-source pins, v1/v1.1 replay, checksum completeness, overlay/group/candidate/queue invariants và conservative dedup.

Kiểm byte bổ sung bằng Git objects của commit cũ 4611111:

- 10/10 files trong v1 giữ nguyên bytes.
- 6/6 derived data files v1.1 giữ nguyên bytes: metadata_overlay.jsonl, template_candidates.jsonl, fragment_groups.jsonl, annex_review_queue.jsonl, duplicate_content_groups.jsonl, docx_mapping_candidates.json.
- Các thay đổi README/manifest/SHA256SUMS tương ứng code guard và tracking review, không thay nội dung pháp lý hoặc promoted acceptance flags.
- 8/8 entries trong manifest files khớp SHA256 và byte size; code_sha256 của cả hai script khớp actual files. Suite replay xác nhận mọi generated artifact tái lập đúng bytes.
- Manifest v1.1 hiện tại SHA256: e801d1e922be85420994d247b27a0e32ad75caf26846fc9fd76381f2fd9f5f41.
- build_legal_forms_v11.py SHA256: 38d4d4dda47b93a32afdb132800057f680103b46e5d2ff47ea718a41eb39c65f.
- export_legal_forms.py SHA256: 9f5e68ebcc17590d0b82a3a6e29ec91b9fe0409c504b5e7fc25538cbf25c46cb.

## Ranh giới nghiệm thu

ACCEPT này là manual engineering review cho export/metadata/provenance/dedup và invariants của gói, trên đúng commit nêu trên. Không xác nhận hiệu lực pháp luật, semantic template selection hoặc chọn phiên bản áp dụng cho một ngày/người cụ thể. Không nghiệm thu DOCX structural/render fidelity, lossless reconstruction hoặc production document generation. Các giới hạn PENDING_REVIEW, TEXT_ONLY, generation_ready=false và production BLOCKED giữ nguyên.

BUGBOT_REVIEW = NOT_RUN_RUNNER_UNAVAILABLE; không gán danh tính hoặc kết quả Bugbot cho manual review này. Nếu owner vẫn yêu cầu riêng Bugbot thì gate đó chưa được thay thế bằng báo cáo này.

Không crawl, ingestion, embedding, paid API, network calls hoặc sửa published snapshot/raw source. Tests chỉ dùng cache temporary fake/replay đã được dọn. Quyền merge/push vẫn cần owner giao riêng; review ACCEPT không tự thực thi integration.
