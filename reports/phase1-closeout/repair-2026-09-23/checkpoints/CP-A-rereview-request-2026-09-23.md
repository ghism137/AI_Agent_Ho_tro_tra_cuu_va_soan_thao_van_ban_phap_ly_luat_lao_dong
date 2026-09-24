# CP-A independent re-review request - 2026-09-23

Status: `REVIEWED_FAIL` — superseded by round-2 request  
Builder: Codex `/root`; runtime model ID and reasoning effort unavailable  
Prepared at: `2026-09-23 16:31:15 +07:00`  
HEAD: `8c49d3a2d727d86c13096bb5814095e32776fa77`

Review the repair for CPA-01 through CPA-04 on these exact dirty hashes:

```text
backend/ingestion/parser.py e4e9be6e84a0780434ac5a7afbb4ca49a03021d8058e38b53b93a79dec206400
backend/ingestion/schema.py 093b79d44259030b74e3a585a45c3a6d29ce58c0e3d5695004ac6e74673213e9
scripts/review_decisions.py d123909b4fe161330f84763c45592888e5a192f5569fe28fe3abb625fcdcced1
scripts/build_registry.py 0d2ad4e14415fed4e33aac26c86155c76093accee26025c73f81bb4a1a6acdff
tests/test_amendment_payload.py 562414f1e78e423e68820f59ef77c16cd4434a5728c0bd966aec0b6e7eb9258b
tests/test_review_decisions.py 6bdfbdf81f54c0927b28df57481a6b11442d6e4d3318035c675a49a6e487d77c
data/raw/official/02-2025-ND-CP-congbao.pdf e7d5d66154cd8f43c0d7ac441e312d9511cfc2dac0005e3fcebf58048a0d9072
```

## Claimed remediation to verify independently

- CPA-01: an open quoted payload cannot take the sequential-outer-item exit;
  the inner amendment verb remains under its payload path until the quote closes.
- CPA-02: an unsupported payload start and an instruction with no following
  payload now quarantine instead of producing duplicate instruction paths.
- CPA-03: subject fingerprints require every named source; verified v2 reviews
  require dependencies; full-content hashes are checked against a separate
  binding map rather than the raw source byte hash.
- CPA-04: `build_registry` now loads a strict review binding index and passes
  dependency, full-content and locator fingerprints through the same production
  function used by `main()`.

## Builder verification

```text
Focused parser/lifecycle: 36 passed, 3 deselected in 2.74s
All tests without the three sandbox tmp_path cases: 63 passed, 3 deselected in 11.50s
Assertions at request preparation with the workspace-backed tmp_path evidence fixture: 66 passed in 9.53s
Canonical NĐ 02/2025 pages 1-9: 69 pieces, 69 unique paths, 4 item-8 payload points
py_compile: PASS
git diff --check: PASS (line-ending warnings only)
```

The reviewer should rerun the two former parser reproductions, missing-source,
missing-dependency, stale-full-content and production binding-path cases. Record
actual reviewer/time/hashes and any findings. Do not infer CP-B or legal fidelity
from CP-A. The builder must not sign this checkpoint.

Independent Bugbot review result is recorded in
`CP-A-bugbot-review-2026-09-24.md`. The resulting fixes are pinned in
`CP-A-rereview-2-request-2026-09-24.md`.
