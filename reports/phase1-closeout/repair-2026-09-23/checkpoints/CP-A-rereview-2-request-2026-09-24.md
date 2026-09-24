# CP-A independent re-review request, round 2 — 2026-09-24

Status: `REVIEWED_FAIL` — one High remains; no repair request is open  
Builder: Codex `/root`; runtime model ID `gpt-5`; reasoning effort unavailable  
Prepared at: `2026-09-24 05:27:23 +07:00`  
HEAD: `8c49d3a2d727d86c13096bb5814095e32776fa77`

Review the remediation of all findings in
`CP-A-bugbot-review-2026-09-24.md` against these exact hashes:

```text
backend/ingestion/parser.py 313b2521f50dd62cb23968aecd9bdc50026cd5df2e11e329ae79cff549a01a85
backend/ingestion/schema.py 1e2f2d5ecfd235c419527d9cddef504bd930c40437b3c99f485c573a3fda0e5b
scripts/review_decisions.py d123909b4fe161330f84763c45592888e5a192f5569fe28fe3abb625fcdcced1
scripts/build_registry.py 0d2ad4e14415fed4e33aac26c86155c76093accee26025c73f81bb4a1a6acdff
tests/test_amendment_payload.py b706496e6a60c45faf7ec829df0db99b3511bc5fb31b52240837e601090cdb61
tests/test_review_decisions.py 26b7266a6b43d15ae2f663c6da56f9d5c4bb05876aab03fcd8ed3113284b8a92
data/raw/official/02-2025-ND-CP-congbao.pdf e7d5d66154cd8f43c0d7ac441e312d9511cfc2dac0005e3fcebf58048a0d9072
```

## Claimed remediation to verify independently

- A top-level-looking `Điều N.` immediately following an amendment instruction
  ending in `như sau:` is retained for the payload state machine instead of
  being intercepted by top-level article detection.
- A sequential clause containing an amendment verb inside an unquoted payload
  is treated as an ambiguous boundary and quarantined; the parser no longer
  silently exits the payload scope.
- Typed evidence locators and dependency IDs reject empty and whitespace-only
  strings.
- `ReviewDecision.applied_values()` returns no materialized fields for a
  rejected decision, so document metadata remains unchanged while the status
  becomes `rejected`.

## Builder verification

```text
Five exact new regressions before repair: 5 failed
Five exact new regressions after repair: 5 passed, 31 deselected in 0.27s
Focused CP-A suite with workspace tmp fixture: 44 passed in 1.96s
Full current suite with workspace tmp fixture: 71 passed in 9.14s
Canonical NĐ 02/2025 pages 1-9: 69 pieces, 69 unique paths, 4 item-8 payload points
py_compile: PASS
git diff --check: PASS (line-ending warnings only)
```

The reviewer must rerun the four reported triggers plus the earlier CPA-01…04
invariants. Record actual reviewer/time/hashes/findings/retest in a new review
record. Do not infer CP-B readiness or legal fidelity from CP-A. The builder
must not sign this checkpoint.

Independent round-2 result: `CP-A-rereview-2-bugbot-review-2026-09-24.md`.
