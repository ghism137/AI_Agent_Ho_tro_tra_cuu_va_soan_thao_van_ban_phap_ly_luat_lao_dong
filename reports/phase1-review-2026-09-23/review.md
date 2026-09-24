# Review Phase 1 repair — 2026-09-23

**Verdict: CHƯA ĐẠT; Phase 1 OPEN.** Review này kiểm phần repair đang dirty và những đường code liên quan trực tiếp đến closeout. Không phải nghiệm thu pháp lý hoặc review toàn corpus. Reviewer: Codex trong phiên hiện tại; không giả nhận là Sol/Terra/Claude. Runtime không cung cấp model ID/effort chính xác để ghi vào hồ sơ này.

Input: HEAD `8c49d3a` và working tree có sẵn. [Evidence JSON](evidence.json) lưu full HEAD, SHA-256 của code/tests/registry/reviews/PDF liên quan, input và output reproductions. Không reset, commit hoặc sửa code/data nguồn. Không chạy registry build, staging build, ingestion, embedding, full eval hoặc pytest. Claim **38/38 PASS** là của handoff 21/09, chưa được chạy lại trong review này.

## Findings chặn nghiệm thu

### R01 — High: parser xử lý đóng quote trước cấu trúc của dòng

`backend/ingestion/parser.py:169–177` append dòng có dấu đóng quote vào piece trước rồi `continue`, bỏ qua phân tích Khoản/Điểm. Reproduction `closing_on_last_clause` trong evidence: `2. Nội dung hai.”` nằm trong `.../article:14/item:1`; không có `item:2`. Đây là sai locator và nội dung provision, không chỉ khác số chunk.

Sửa: nhận diện cấu trúc dòng trước khi đóng scope; không dùng closing quote để bỏ qua Khoản/Điểm của dòng đó. Test phải assert đúng text và locator của cả hai khoản.

### R02 — High: parser chưa xử lý các ranh giới payload hợp lệ

`parser.py:83,119–159,294–301`: regex chỉ nhận quote là ký tự cuối; nhánh khởi tạo payload luôn `continue` nên không kiểm quote đóng ngay trên dòng đầu. Reproductions `quote_semicolon` và `single_line_payload` đều raise quarantine với payload đã đóng. `point_instruction` cho thấy chỉ dẫn sửa đổi tại điểm a không mở payload; toàn nội dung bị giữ trong point a. Payload base hiện dựng từ outer item, chưa giữ đầy đủ instruction path.

**Đối chiếu input thật:** đọc đúng `data/raw/official/02-2025-ND-CP-congbao.pdf`, pages 1–9 theo stage builder; gọi extractor rồi parser trong bộ nhớ trả `Amendment payload in Điều 1 did not close ... body/article:1/item:8/amendment_payload`. Không rebuild corpus. Lỗi này xác nhận claim parser done chưa đủ; chưa kết luận mọi lỗi trên PDF có cùng nguyên nhân với fixtures.

Sửa: một state machine thống nhất cho outer headings và payload, giữ đầy đủ instruction path, xử lý single-line/quote+punctuation/multiline/point instructions; ambiguity thật vẫn quarantine. Giữ namespace `amendment_payload`, không đổi sang AD-1 options cũ chỉ để né lỗi.

### R03 — High: Gate 3 có thể PASS khi required operations còn pending/blocked

`scripts/build_phase1_stage.py:175–178,210`: bỏ qua pending/blocked khi validate, nhưng đưa mọi operation có relation_id vào `op_rels`. Vì vậy một operation blocked vẫn được tính là đã đáp ứng mandatory relation. Hiện 15 operations gồm **13 pending, 2 blocked**, không có verified operation. Manifest đang lưu Gate 3 PASS thuộc snapshot cũ, không phải chứng cứ pipeline hiện hành đã giải quyết chúng.

Sửa: required effect chỉ hoàn tất nếu operation đúng scope, được review còn hiệu lực và đã áp dụng/được chứng minh không áp dụng. Pending/blocked phải sinh blocker cho coverage liên quan. Kiểm missing operations file và relation chưa có disposition, không chỉ record hiện có.

### R04 — High: materializer chấp nhận hash thiếu, giữ provenance cũ cho text mới

`backend/ingestion/version_builder.py:110–115,194–215`: guard chỉ từ chối literal `unknown`; missing/null/giá trị giả khác không bị kiểm đối chiếu bytes. Reproduction trong evidence dùng verified replace không có source_hash/target_hash vẫn trả version NEW; source_refs của NEW vẫn là nguồn OLD. `new_v = dict(v)` không thể chứng minh nguồn nội dung amendment. Nếu không có payload, code còn fallback về text đích. `materialized = list(input_versions)` cũng sửa dict input (repro valid_to input đổi thành 2021-01-01).

Sửa: validate hash/ref/locator/precondition với nguồn thật, bắt buộc payload đúng operation; dựng mapping nội dung → source refs mới, giữ base lineage riêng; bảo toàn lịch sử và input bất biến. Không coi việc chunker đã bỏ source_id giả là đã giải quyết provenance end-to-end.

### R05 — High: metadata verification bị nâng thành coverage verification

`scripts/build_registry.py:136–139` chỉ cần document verified là coverage record được verified. Metadata review không chứng minh completeness của amendment chain, population hay applicability tại as-of date. Đây là lỗi còn tồn tại, không phải thay đổi mới của parser.

Sửa: coverage có decision/evidence riêng; không suy verified từ document. Chỉ áp dụng trạng thái cho versions/chunks khi đủ prerequisite đúng scope.

### R06 — High: gate và publisher chưa ràng buộc independent acceptance cùng digest

`build_phase1_stage.py:236` đọc `legal_verification.status == PASS` không kiểm nó chứng nhận candidate/evidence nào. `scripts/audit_gate1.py:239–244` in report nhưng không exit nonzero khi gate FAIL. Publisher `scripts/publish_phase1_release.py:32–72` dựa audit/coverage, chưa yêu cầu acceptance envelope độc lập; danh sách snapshot không gồm operations.json và legal_verification.json. `candidate_fingerprint()` chưa chứa operations, schema, temporal, review/audit semantics; operations hash riêng trong manifest không thay thế content/evidence fingerprint đầy đủ.

Sửa: tách content digest, evidence digest, acceptance envelope để tránh vòng hash; validate cả ba trước publish, snapshot đầy đủ dependencies, fail-closed CLI và fault tests. Không publish trong phiên review này.

## Findings bổ sung và trạng thái thực tế

- **R07 / Medium — retired generator hỏng cấu trúc:** `scripts/retired_auto_metadata_review.py:28–38` mất khai báo ROOT và `def auto_review_metadata`, phần generator nằm sau `raise` trong guard; cuối file vẫn gọi hàm không tồn tại. Default guard chặn được, nhưng override được quảng cáo không hoạt động; bất kỳ chuỗi env không rỗng cũng qua guard. Nên retire vô điều kiện, hoặc có entrypoint rõ và không tái sinh auto-verified. Không chạy generator để kiểm vì nó là writer nguy hiểm.
- **R08 / Medium — source conflict còn phụ thuộc thứ tự:** `scripts/review_decisions.py:99` cho phép hai source decisions khác values nếu conclusion giống nhau và decision đầu có values rỗng. Document branch đã kiểm strict true-duplicate; source branch cần cùng quy tắc. Đây là latent code path: hiện active review files đều là document metadata, chưa có source decision trong tập này.
- Archive manifest có **61 entries: Class A 41, Class B 20**; mọi archived filename đều tồn tại. Chưa hash/đối chiếu toàn archived content hoặc xác minh 41 replacement legally correct.
- Active review set tải được **41 document/metadata decisions**. Áp dụng chúng trong bộ nhớ trên defaults từ 61 documents/sources hiện có cho **41 verified, 20 pending**, không ném conflict. Đây không phải kết quả chạy build_registry vì chưa inventory/re-hash raw. Danh sách 20 IDs nằm trong evidence.
- `documents.json` vẫn ghi **61 verified**: file generated chưa phản ánh archive. Không coi 20 pending là đã được materialize trong registry như handoff mô tả.
- Không có bằng chứng Class C đang chặn trong tập decisions được áp dụng này. Handoff gộp khác review_type thành conflict là chưa đủ; document/identity hiện không được `apply_document_decisions` áp dụng. Task đầu cần phân biệt conflict, duplicate, stale, unsupported và thiếu review.
- Stored candidate: `candidate-3995dbe3f41d51cd`, 61 docs / 20.410 chunks / 20.318 versions. Fingerprint tính từ code/inputs hiện tại là `candidate-c350e21f2516a157`: staging **stale**. Mốc 3.110 chunks của handoff là lịch sử, không phải baseline hiện tại.
- Active pointer vẫn `phase1-febf5129f0e33d40`; chỉ đọc pointer, chưa re-hash toàn release. Không suy release đã được nghiệm thu.

## Phần có thể giữ và phần chưa kết luận

Giữ hướng namespace amendment_payload, fail on conflicting document metadata và bỏ fabricated source_id của chunker. Chưa duyệt implementation parser; giữ archive như audit trail. Các tests hiện có thiên về quote đóng riêng dòng nên chưa bao phủ reproductions trên. Handoff tự ghi Gemini/Antigravity, người dùng nêu Claude Sonnet tham gia thiết kế: provenance tác giả chưa được xác minh, review này đánh giá artifact chứ không gán tác giả thay người dùng.

Các con số 505 collision / 2.215 temporal errors từ packet M0 là **historical, chưa đo lại**. Không đóng P1-01…P1-08 cũ chỉ bằng A–F. Chưa source/legal review đủ 61 documents, dependencies, 15 coverage và 6 nhóm; chưa kiểm tất cả operation types, full suite, determinism hoặc publish faults.

## Cách tái kiểm

Lệnh review dùng `venv/Scripts/python.exe -X utf8 -B -` với snippet đọc JSON, gọi `parse_legal_document(text, {'doc_number':'TEST'})` cho inputs trong evidence; PDF dùng `extract_pdf_text(Path(path), first_page=1, last_page=9)` rồi parse trong bộ nhớ. Materializer input/output được lưu nguyên trong evidence. Metadata: dùng documents hiện có nhưng reset title về doc_number, issued_date/valid_from về null, aliases về [], status pending, rồi apply_document_decisions với sources và reviews hiện có. Các phép này không gọi main/build/publish.

Các lần kiểm thành công exit 0; lần thử đầu gặp stdout cp1252 (đã chuyển `-X utf8`) và lần gọi extractor đầu thiếu keyword page interval (đã sửa theo stage builder). Những lỗi thao tác này không phải findings sản phẩm. Full suite và full legal audit: **NOT_RUN**.

Kế hoạch thực thi: [.claude/project/phase1_completion_plan_2026-09-23.md](../../.claude/project/phase1_completion_plan_2026-09-23.md).
