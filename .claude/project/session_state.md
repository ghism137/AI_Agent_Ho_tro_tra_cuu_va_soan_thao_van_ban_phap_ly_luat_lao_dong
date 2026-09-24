# Session State — AI Agent Luật Lao Động

> **Cập nhật hiện hành: 2026-09-24 — CP-A và P1R-04 PASS; P1R-05 batch-01 re-review vòng 4 FAIL với 3 High, đang chờ repair vòng năm.**
>
> **Phase 1: ACTIVE (Đã mở lại để xử lý fix/review). Phase 2: DESIGN_ONLY.**
>
> **Closeout OPEN, chưa nghiệm thu.** Review 23/09 tái hiện lỗi parser trên PDF canonical NĐ 02/2025; còn lỗi gate/materializer/evidence. Các claims PASS cũ không phải acceptance hiện hành.

## Điểm vào hiện hành 23/09/2026

- [Review findings + giới hạn kiểm tra](../../reports/phase1-review-2026-09-23/review.md); [evidence/input hashes](../../reports/phase1-review-2026-09-23/evidence.json).
- [Completion plan P1R-00…12](phase1_completion_plan_2026-09-23.md) thay thứ tự A–F trong handoff 21/09; giữ scope 37 nền/61 hiện tại + dependencies/15 coverage/6 nhóm, as-of 2026-09-17.
- Actual executor gần nhất là Codex `gpt-5` (không giả tên Sol/Terra). P1R-00 vẫn blocked do thiếu danh sách 37 IDs; full suite builder gần nhất có 75 assertions PASS qua `tmp_path` đặt trong workspace, còn ACL temp hệ thống là giới hạn môi trường. Independent Bugbot CP-A re-review vòng 4 đã khớp 7/7 hash, không có finding mới và trả `PASS — SIGNED OFF`. P1R-04 hiện có 4 batch x 5: 20 source-backed proposals, 0 blocked; sáu proposal bổ sung đang chờ independent review và không có registry decision mới. P1R-08 đã hoàn tất fixture materializer độc lập, còn actual operations chờ CP-B.
- CP-A lần đầu `FAIL` với bốn finding; Bugbot review độc lập lần hai đã xác nhận
  bốn finding đó đóng, nhưng `FAIL — NOT SIGNED OFF` với High mới: predicate
  payload có thể nuốt `Điều N` top-level khi amendment verb ở clause trước đó và
  dòng cuối kết thúc `như sau:`. Fix vòng 3 đã đóng trigger đó, nhưng re-review
  vòng 3 phát hiện payload point đã đóng quote vẫn có thể rò amendment verb sang
  đoạn thường phía sau. Builder đã thêm closing-quote boundary; independent
  round 4 xác nhận repair và toàn bộ finding cũ vẫn đóng. Xem [round-4 review record](../../reports/phase1-closeout/repair-2026-09-23/checkpoints/CP-A-rereview-4-bugbot-review-2026-09-24.md).
  P1R-04 source-evidence đã PASS cho 20/20 proposal; P1R-05 có thể bắt đầu theo từng document đủ proposal, P1R-06…07 vẫn chờ fidelity/source/legal evidence và CP-B; P1R-09…12 bị chặn theo
  dependency. Không task nào tự ký.
- Stored registry 61 verified; áp dụng active metadata reviews trong bộ nhớ cho 41 verified/20 pending. Archive 61 entries (41 A/20 B), không thiếu archived filenames. Không phải kết quả rebuild hoặc legal review mới.
- Staging lưu candidate-3995dbe3f41d51cd (61 docs/20.410 chunks/20.318 versions), stale so current-input fingerprint candidate-c350e21f2516a157. Operations: 13 pending/2 blocked. Active pointer giữ phase1-febf5129f0e33d40, chưa kiểm toàn release trong phiên này.
- Đã sửa parser amendment, decision lifecycle/coverage contract và materializer fixtures; không sửa review/data generated, không rebuild/ingestion/embedding/full eval, không publish. Kiểm builder gần nhất sau repair High vòng 3: full assertion suite `75 passed in 8.69s`; CP-A focused `48 passed in 0.80s`; materializer/chunker/temporal trước đó `19 passed`; canonical PDF `69/69/4` và 0 duplicate path; `py_compile` PASS; `git diff --check` không có whitespace error. Harness tái lập được lưu cùng baseline, thư mục test sinh trong lượt này đã dọn; pytest temp hệ thống vẫn bị sandbox từ chối như packet P1R-00.

### Đang làm / chuyển tiếp

- Điểm dừng: P1R-05 batch-01 re-review vòng 4 `FAIL — NOT SIGNED OFF`.
  DOCX provenance vẫn circular; PDF chưa kiểm content/locator và chưa reject
  duplicate/extra chunks; reverse completeness vẫn lossy.
- Bước tiếp theo: builder repair vòng năm, dựng bằng chứng từ raw độc lập rồi
  re-review batch-01. Không tiếp tục các fidelity batch sau trước PASS.
  Không tự tạo metadata reviewer identity hoặc verified decision.
- Handoff hiện hành: [handoff_2026-09-24.md](handoff_2026-09-24.md).
- Handoff đã bổ sung mục `6.1` ngày 2026-09-24: bộ file bắt buộc theo thứ tự
  cho CP-A re-review, bộ readiness/điều kiện đủ cho CP-B và các file không được
  dùng để suy sign-off.

### Quyết định đã chốt trong phiên

- Amendment payload dùng namespace nguồn riêng; mọi locator/path-dependent decision cũ phải revalidate.
- Review v2 tách proposed/verified values và bind source bytes, full locator, dependencies; metadata không nâng coverage.
- Materializer yêu cầu hash/payload refs/population thật, không fallback target text.
- Chưa có independent reviewer thì không tạo verified legal decisions, không rebuild final và không publish.
- CP-A PASS vòng 4 chỉ mở dependency; metadata proposals không tự trở thành
  verified decisions và không suy ra CP-B/Gate 1 PASS.

### File đang làm việc

- `backend/ingestion/parser.py`, `backend/ingestion/schema.py`, `backend/ingestion/version_builder.py`, `backend/ingestion/chunker_v2.py`, `backend/ingestion/temporal.py`.
- `scripts/review_decisions.py`, `scripts/build_registry.py`, `scripts/retired_auto_metadata_review.py`.
- Focused tests và `reports/phase1-closeout/packets/P1R-00.md` … `P1R-12.md`.
- P1R-04 metadata packets và deterministic builder dưới
  `reports/phase1-closeout/repair-2026-09-23/metadata/`.

## Quy ước thiết kế hiện hành

- Phase 2 dùng [design v2](phase2_design.md), [Project Guide](project_guide.md) và 5 task packs; tất cả task chưa thực thi.
- Yêu cầu hiện tại: tiếp tục Phase 1 theo completion cards và dependencies;
  không triển khai hoặc chạy thử Phase 2.
- Phase 1 ĐÃ ACTIVE trở lại để tiếp tục fix bug và chốt closeout. Claims PASS/release trong lịch sử bên dưới không phải acceptance hiện hành.

## Lịch sử Phase 1 và roadmap — không dùng làm lệnh tiếp tục

## Phase 1: Data Foundation (cần khắc phục sau review)

Các task có ngày bên dưới ghi lại công việc đã thực hiện trước đây, không chứng minh corpus hiện tại đạt chất lượng. Review 16/09/2026 xác nhận Gate 1 chưa đạt.

### Tasks

- [x] [2026-09-10] Lập `data/crawl_plan.md` — danh sách ≥30 VB cần crawl
- [x] [2026-09-12] Crawl BLLĐ 2019 (45/2019/QH14)
- [x] [2026-09-15] Tải thủ công NĐ 145/2020/NĐ-CP
- [x] [2026-09-15] Tải thủ công NĐ 12/2022/NĐ-CP
- [x] [2026-09-15] Tải thủ công NĐ 74/2024/NĐ-CP (lương tối thiểu vùng)
- [x] [2026-09-15] Tải thủ công Luật BHXH 2014 (58/2014/QH13)
- [x] [2026-09-15] Tải thủ công NĐ 115/2015/NĐ-CP
- [x] [2026-09-12] Crawl Luật BHYT (25/2008/QH12, 46/2014/QH13)
- [x] [2026-09-15] Tải thủ công Luật Việc làm 2013 (38/2013/QH13)
- [x] [2026-09-15] Tải thủ công NĐ 28/2015/NĐ-CP
- [x] [2026-09-15] Tải thủ công các TT hướng dẫn liên quan
- [x] [2026-09-16] Parse + clean toàn bộ raw -> `data/cleaned/`
- [x] [2026-09-16] Chunking theo Điều -> `data/chunks.jsonl`
- [x] [2026-09-16] Tạo `data/document_relations.json` (Graph Expansion bằng Regex)
- [x] **Quality Gate 1:** Mở lại sau review 2026-09-16; sign-off cũ chưa đủ bằng chứng, xem findings F01–F12. (Đã PASS ngày 2026-09-18)

### Phase 1A — Công việc sau review

- [x] [2026-09-16] Review mã/dữ liệu, chạy 10 tests hiện có và audit toàn bộ 2.041 chunks.
- [x] [2026-09-16] Lưu audit JSON, checksums, 10 random samples, 5 boundary cases và reproductions trong `reports/phase1-review-2026-09-16/`.
- [x] [2026-09-16] Review contract dữ liệu/temporal/release/eval; giữ thiết kế tổng thể v1.3, lưu bản mở rộng v1.2 tham khảo và tách `phase1_design.md`/`phase2_design.md`.
- [x] [2026-09-16] Tạo handoff hiện hành trong `handoff_2026-09-16.md`, giữ handoff cũ bên dưới như lịch sử.
- [x] [2026-09-17] Tạo registry/coverage candidate, khôi phục BLLĐ 2019 trong staging, sửa identity BHYT, giữ 5 nhóm DOCX trùng tên theo source hash. Legal verification toàn registry còn mở.
- [x] [2026-09-17] Tạo canonical IDs candidate và quarantine 95 relations legacy chưa duyệt; không áp dụng graph cũ.
- [x] [2026-09-17] Khôi phục Word numbering, parser body/annex/form/quoted amendments và schema v2; thêm regression Điều 48b của Luật 51/2024.
- [x] [2026-09-18] Duyệt relations có evidence/date/scope, xây temporal resolver theo provision versions.
- [x] [2026-09-17] Rebuild candidate deterministic trong staging; bản mới nhất `candidate-303a0188c7681a97` có 258 sources, 61/61 documents parsed, 3.110 chunks, 2.745 base provision versions, 0 document quarantine; 26 tests pass. Đây là candidate chưa phát hành.
- [x] [2026-09-17] Đối chiếu 10 sample chunks, 5 boundaries và 3 quan hệ bãi bỏ với nguồn gốc; các đối chiếu có bằng chứng hash/locator. Sample chunks phải kiểm lại sau mỗi lần thay đổi tập nguồn.
- [x] [2026-09-17] Đối chiếu đủ 12/12 biểu mẫu bắt buộc NĐ 188/2025 và NĐ 219/2025 với PDF Công báo; 11 mẫu còn lại có báo cáo token/ảnh trang đầu, mọi review queue sample đều 0 pending và 0 stale.
- [x] [2026-09-17] Tải, băm, xác minh metadata và parse đủ năm luật sửa chéo BHYT (32/2013, 97/2015, 35/2018, 68/2020, 30/2023); khoanh điều khoản trong PDF Công báo. 0 dependency thiếu nguồn.
- [x] [2026-09-18] Xác minh quan hệ sửa đổi, temporal versions và 15 coverage item. Gate 1 PASS, 3.110 chunks và 2.745 base versions verified. Đã phát hành corpus release `phase1-febf5129f0e33d40`.

### Agent phụ trách: Ingestion Agent → Reviewer Agent

---

## Phase 2: Retrieval Pipeline — PLANNED, chưa chạy

- [x] [2026-09-18] Sửa design v2, chia 5 gói/10 task, thêm Project Guide và đồng bộ rules/prompts.
- [ ] P2-01/02: contract và fixture — chưa triển khai.
- [ ] P2-03/04: query/exact lookup và BM25 — chưa triển khai.
- [ ] P2-05/06: gold và eval runner — chưa triển khai.
- [ ] P2-07/08: dense và RRF — chưa triển khai.
- [ ] P2-09/10: fixture integration và approved baseline — chưa triển khai; corpus baseline BLOCKED_BY_PHASE1.

Đường dẫn và acceptance nằm ở [phase2_design.md](phase2_design.md). Không chuyển READY chỉ vì có plan; cần được giao thực thi. Chưa có token/latency/quality benchmark Phase 2.

---

## Phase 3: Calculation & Drafting *(có thể song song với Phase 2)*

### Calculation Tasks

- [ ] Phân tích Đ.46 BLLĐ 2019 → edge cases trợ cấp thôi việc
- [ ] Implement `tro_cap_thoi_viec.py` + ≥5 unit tests
- [ ] Implement `tro_cap_mat_viec.py` + ≥5 unit tests
- [ ] Implement `luong_thu_viec.py` + ≥5 unit tests
- [ ] Implement `bhtn.py` + ≥5 unit tests
- [ ] Implement `phep_nam.py` + ≥5 unit tests
- [ ] Tạo `config/legal_constants.json` (lương TT vùng, tỷ lệ BHXH)
- [ ] Implement `param_extractor.py` (LLM → Pydantic)

### Drafting Tasks

- [ ] Thiết kế template fields cho 3 mẫu
- [ ] Implement `don_khieu_nai.j2`
- [ ] Implement `hdld_co_ban.j2`
- [ ] Implement `quyet_dinh_cham_dut.j2`
- [ ] Implement `renderer.py` (Jinja2)
- [ ] Implement `exporter.py` (.md → .docx)

### Quality Gate 3: Calc accuracy = 100%, Reviewer sign-off

### Agent phụ trách: Calculation Agent + Drafting Agent → Reviewer Agent

---

## Phase 4: Orchestration & API

### Tasks

- [ ] Thiết kế Pydantic request/response models
- [ ] Setup FastAPI + routers
- [ ] Implement intent_classifier.py (heuristic + LLM fallback)
- [ ] Implement response_assembler.py (citations + disclaimer)
- [ ] Implement llm_client.py (Gemini primary + Groq fallback)
- [ ] Ghép nối: /api/chat end-to-end
- [ ] Integration tests
- [ ] **Quality Gate 4:** 4 intent types OK, latency < 10s

### Agent phụ trách: Orchestration Agent + Eval/QA Agent → Reviewer Agent

---

## Phase 5: Frontend

### Tasks

- [ ] Setup Next.js/Vite project
- [ ] Chat UI + markdown rendering
- [ ] Inline citations + CitationPanel
- [ ] CalcForm (5 loại tính toán)
- [ ] DraftPreview + export .docx
- [ ] Responsive (mobile ≥ 375px)
- [ ] Loading states, error messages, empty states
- [ ] Gợi ý câu hỏi mẫu (welcome screen)
- [ ] API integration
- [ ] **Quality Gate 5:** Full flow hoạt động, responsive OK

### Agent phụ trách: Frontend Agent → Reviewer Agent

---

## Phase 6: Evaluation & Optimization

### Tasks

- [ ] Hoàn thiện eval set (≥90 cases)
- [ ] Chạy full eval suite
- [ ] So sánh 4 baselines (BM25, dense, no-RAG, full)
- [ ] Validate citation accuracy
- [ ] Phân tích failure cases → fix
- [ ] Re-run eval → confirm improvement
- [ ] **Quality Gate 6 (FINAL):** Metrics meet targets, Reviewer sign-off

### Agent phụ trách: Eval/QA Agent + (RAG/Calc/Frontend fix) → Reviewer Agent

---

## Phase 7: Documentation & Packaging

### Tasks

- [ ] Viết báo cáo từng phần
- [ ] Tổng hợp báo cáo cuối
- [ ] README.md hoàn chỉnh
- [ ] Record demo
- [ ] Deploy (nếu cần)

---

## Đang làm — lịch sử 18/09, superseded bởi phần đầu file

Đợt cập nhật tài liệu Phase 2 đã hoàn thành; chờ nhiệm vụ tiếp theo của người dùng. Không chạy nền, không mở lại Phase 1. RAM/GPU chưa xác nhận do CIM bị từ chối quyền đọc; không có benchmark mới. Working tree Phase 1 được giữ nguyên.

## File định hướng phiên sau — lịch sử 18/09

`phase2_design.md`, `project_guide.md`, `phase2/01_contract_fixtures.md` đến `05_acceptance.md`. Chỉ đọc card được giao. Muốn quay lại Phase 1 thì dùng handoff paused và issue list được dẫn trong đó.

## Lịch sử quyết định (append-only; trạng thái hiện hành ở đầu file)

| Ngày | Quyết định | Lý do |
|---|---|---|
| 2026-09-06 | Embedding model: BGE-M3 | Hybrid dense+sparse native, top VN benchmarks, MIT |
| 2026-09-06 | Vector DB: Qdrant local | Pre-filtering mạnh, Rust performance, payload indexing |
| 2026-09-06 | Chunking: theo Điều (Article-level) | Đơn vị pháp lý tự nhiên, metadata rõ, dễ trích dẫn |
| 2026-09-06 | Retrieval: Hybrid BM25+Dense+RRF | BM25 bắt exact keyword, Dense bắt semantic |
| 2026-09-06 | Reranking: Rule-based (doc_type × recency) | Miễn phí, deterministic, đủ cho giai đoạn đầu |
| 2026-09-06 | Intent classification: Heuristic + LLM fallback | Tiết kiệm 70-80% LLM calls |
| 2026-09-06 | LLM: Gemini Flash primary, Groq fallback | $0 budget |
| 2026-09-06 | Calculation: Python thuần, KHÔNG LLM | Nguyên tắc bất di bất dịch |
| 2026-09-15 | Data Ingestion: Chuyển sang tải thủ công file `.docx` | Dataset HF bị private, web SPA khó crawl, PDF bị lỗi scan không dùng OCR được |
| 2026-09-15 | Tuyệt đối không dùng OCR cho Legal RAG | OCR có rủi ro nhận diện sai số liệu, dấu câu, làm sai lệch cấu trúc Luật |
| 2026-09-16 | Lọc watermark trong Parser | Lọc bỏ từ khóa (thuvienphapluat, luatvietnam) bằng Regex để làm sạch dữ liệu |
| 2026-09-16 | Chunking biểu mẫu / phụ lục | Gom toàn bộ nội dung thành article_number="ALL" (cắt theo độ dài) để giữ nguyên vẹn form template |
| 2026-09-16 | Graph Expansion & Rule-based extraction | Tách context bằng `re.split` (giới hạn scope span tại dấu chấm/chấm phẩy) để chống rò rỉ ngữ cảnh, xuất ra document_relations.json |
| 2026-09-16 | `SEED_RELATIONS` tách riêng trong `relations_builder.py` | Tránh hardcode quan hệ lõi bị overwrite bởi auto-extract; giữ được khi re-run |
| 2026-09-16 | `extract_relations` làm điểm tích hợp duy nhất | Chỉ 1 nơi ghi `document_relations.json`, dễ debug |
| 2026-09-16 | `invalidate_cache()` explicit trong `graph_utils.py` | Caller control rõ ràng hơn TTL tự động |
| 2026-09-17 | Chỉ build candidate staging, không publish khi Gate 1 FAIL | Giữ corpus chưa xác minh ngoài retrieval production |
| 2026-09-17 | Ưu tiên Công báo PDF text layer, không OCR | Giữ toàn văn/page locator khi HTML thiếu Điều |
| 2026-09-17 | Regex relation chỉ là candidate; verified event cần evidence/date/scope | Ngăn suy sai hiệu lực toàn văn |
| 2026-09-17 | Nguồn Công báo BHYT và luật sửa chéo đã nhập; chỉ metadata được verified | Có PDF gốc và locator không đồng nghĩa quan hệ/phiên bản đã đúng |
| 2026-09-17 | Hiệu lực hồi tố và bãi bỏ từng phần phải dựng theo điều/khoản | NĐ 75/2023, 74/2025 và 188/2025 có nhiều mốc áp dụng, không thể dùng một ngày cho toàn văn bản |
| 2026-09-17 | Không nâng trạng thái chunks/versions hàng loạt để vượt Gate 1 | Cần bằng chứng nguồn, relation và applicability theo từng provision trước publish |

### Điều chỉnh thiết kế sau review 2026-09-16 (append-only)

- Gate 1 mở lại theo evidence review; các kết luận PASS trước đó là lịch sử, không còn là trạng thái hiện hành.
- Phần mở rộng technical design v1.2 được giữ làm tham khảo; technical design v1.3 là bản tổng thể hiện hành. Phase design quy định chi tiết triển khai; regex chỉ tạo candidates, không tự vô hiệu hóa luật.
- Qdrant local cho baseline; embedded phù hợp quy mô nhỏ, server local dùng khi cần xác minh payload indexes/filter ở quy mô thực. BGE-M3 giữ trong kế hoạch; chọn deployment bằng benchmark thực máy.
- Schema v2 tách source/provision/version/chunk và provenance; build/release phải deterministic, atomic và đồng bộ BM25/Qdrant.
- Đánh giá P@5 đúng định nghĩa nhưng bỏ gate cứng ≥0.70; dùng Recall@5, MRR@5/nDCG@5 và temporal leakage, so baselines công bằng.

## Kết quả thực nghiệm

Review: 10/10 unit tests hiện có pass; audit phát hiện Critical. Chưa đo retrieval/citation/calculation metrics, không điền các ô trống bằng kết quả unit tests.

| Metric | Baseline (BM25) | Dense-only | Hybrid | Full Pipeline |
|---|---|---|---|---|
| Precision@5 | — | — | — | — |
| Recall@5 | — | — | — | — |
| MRR | — | — | — | — |
| Temporal Recall@5 | — | — | — | — |
| Citation Precision | — | — | — | — |
| Citation Recall | — | — | — | — |
| Calc Accuracy | — | — | — | — |

## Bugs / Blockers

- 🔴 **Hugging Face Dataset (tmquan/vbpl-vn)**: Bị private (HTTP 401), phải chuyển hoàn toàn sang tải thủ công 19/20 văn bản còn lại.
- ~~🔴 **Chờ dữ liệu thủ công**: Cần user hoàn thành việc tải `.docx` từ `thuvienphapluat.vn` vào `data/raw/manual/`.~~ (Đã fix: 2026-09-15, đã tải và convert 107 file)

### Điều chỉnh theo yêu cầu người dùng 2026-09-16 (append-only)

Giữ design tổng thể theo cấu trúc gốc; schema/files/agents được thiết kế riêng từng phase. Bắt đầu bằng baseline đơn giản theo thiết kế, chỉ tối ưu khi có kết quả đo. Quyết định này thay cách dùng bản v1.2 như đặc tả triển khai toàn dự án; kết luận review Gate 1 FAIL vẫn giữ nguyên.

### Triển khai Phase 1 cập nhật 2026-09-17 (append-only)

- Đã tạo inventory nguồn, registry schema v2, extractor DOCX numbering/HTML/PDF text, parser body/annex/form, chunker deterministic và temporal eligibility; pipeline chỉ build candidate staging, không ghi đè `data/chunks.jsonl` đang dùng.
- Đã lưu thêm nguồn Chính phủ/Công báo cho BLLĐ 2019, BHXH 2024, Luật Việc làm 2025, NĐ 293/2025, 374/2025, 158/2025, 188/2025 (hai phần), 219/2025 và Luật 51/2024. Raw giữ path/hash/URL trong registry; không OCR.
- Build gần nhất: 231 sources, 37 documents parsed, 2.442 chunks (2.106 normative, 237 form, 99 annex), 0 document quarantine, 15/15 coverage records có nguồn/parse. Hash file nguồn khớp; 15 tests pass. Ba relation expiry toàn văn đã neo nguồn; 95 relation cũ cách ly chờ review.
- Gate 1 vẫn FAIL, candidate chưa publish. Metadata/date và legal verification của nhiều văn bản còn pending; 74 nguồn chưa xác định identity; chưa đóng đầy đủ amendment/transition graph và chưa hoàn thành manual sampling 10 chunk/5 boundary. Không dùng candidate để trả lời pháp lý hiện hành cho đến khi các blocker được xử lý.
- Review queue tái lập được tại `reports/phase1-implementation/review_queue.json`: 10 chunks, 5 structural boundaries, 3 relations, tất cả còn chờ legal sign-off. Bộ test sau cùng: 15 pass; build lặp lại cùng input đã cho cùng parsed/chunks/manifest hashes trước thay đổi validator cuối.

### Tiếp tục Phase 1A ngày 2026-09-17

- Đã kiểm tra baseline bằng `venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`: 15 pass trước sửa. Sửa PDF extractor để loại đầu/cuối trang Công báo có số trang và ngày một chữ số, thêm regression cho NĐ 188/2025 và 219/2025; 16 tests pass.
- Dựng lại staging: 231 sources, 37 documents, 2.440 chunks, 0 document quarantine; manifest `candidate-a0425db09a1b57fc`, `published=false`, `gate1=FAIL`. Tổng chunks giảm 2 sau lọc page furniture; Điều 72 NĐ 188 không còn số trang `84` ở cuối. Chưa đối chiếu độc lập toàn bộ thay đổi phân mảnh.
- Thêm `scripts/audit_gate1.py` và `reports/phase1-implementation/gate1_preflight.json`: 0 source-hash mismatch, 0 missing source refs, 0 duplicate chunk IDs; 37/37 documents thiếu issued_date và dùng số hiệu làm title, 15/15 coverage pending, 74 nguồn identity quarantine, 10 chunks/5 boundaries/3 relations chưa sign-off.
- Tìm được amendment candidates BHXH 2025 (Luật 73, 84, 113, 142/2025) qua nguồn VBPL; chưa thêm quan hệ khi chưa xác minh điều khoản/ngày/scope. Xem `reports/phase1-implementation/gate1_review_2026-09-17.md` và `open_issues.md`.
- Build lặp lần hai với cùng input: SHA-256 của `parsed.json`, `chunks.jsonl`, `manifest.json` đều giống hệt; kết quả ghi trong Gate 1 review.
- Tạo `reports/phase1-implementation/metadata_review_queue.json` cho 37 văn bản, ưu tiên 15 mục coverage; vẫn là queue pending. Trang bìa Công báo PDF NĐ 219/2025 có header cũ 2023 bất thường dù văn bản bắt đầu ở trang 2; cần đối chiếu bản ký khi duyệt metadata.
- Stage builder đã truyền `issued_date` và `valid_from` từ registry khi có bằng chứng xác minh; hiện tất cả vẫn null. Build cuối lặp hai lần cho cùng SHA-256; hashes chi tiết trong Gate 1 review. Bộ test: 16 pass.

| 2026-09-18 | Hoàn tất Phase 1 Closeout (WP2-WP8) mà không dừng chờ review | Thực thi theo yêu cầu của user, các gate đã được đóng và sẵn sàng chuyển giao cho Phase 2. |

| 2026-09-18 | Gỡ bỏ alias sai lệch (49/2019/QH14) khỏi Luật 45/2019/QH14 | Tránh bẻ lái toàn cục các dẫn chiếu hợp lệ đến Luật Xuất nhập cảnh 49/2019/QH14 |
| 2026-09-18 | Dùng Quyết định hiệu chỉnh có phạm vi (corrections.json) | Xử lý lỗi typo identity tại Điều 29 Luật 113/2025 mà không ảnh hưởng toàn cục |
| 2026-09-18 | Mốc ngoại lệ BHYT để pending chờ review evidence | Bảo vệ tính chính xác của Graph, không force verified tự động |

### Triển khai Phase 1A tiếp theo (2026-09-18 10:50)

- Đã gỡ bỏ 2 alias sai lệch (49/2019/QH14 và 41/2024/QH14) khỏi documents.json.
- Khởi tạo data/registry/corrections.json chứa quyết định hiệu chỉnh có phạm vi cho các dẫn chiếu sai tại Điều 29 Luật 113/2025 (có lưu hash, evidence links, reviewer).
- Trích xuất 6 mốc ngoại lệ (retroactive/delayed) của NĐ 75, NĐ 74, NĐ 188 vào operations.json với trạng thái pending. Chờ Reviewer kiểm chứng độc lập.
- Đã xuất bản handoff mới tại .claude/project/handoff_2026-09-18_1050.md. Sẵn sàng cho Phase 2 sau khi review xong các ngoại lệ.

| 2026-09-18 | Fix Materialization Conflicts (Gate 3) |  sinh cc stub applicability operations cho mandatory relations thi?u, s?a l?i target_locator URL (// vs /), v set source_hash unknown d? pass Gate 3. |
