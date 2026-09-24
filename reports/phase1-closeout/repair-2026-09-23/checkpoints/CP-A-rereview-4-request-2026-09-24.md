# CP-A independent re-review request, round 4 — 2026-09-24

Status: `READY_FOR_INDEPENDENT_REVIEW — NOT SIGNED OFF`  
Builder: Codex `/root`, runtime model ID `gpt-5`; reasoning effort unavailable  
Prepared at: `2026-09-24 08:31:27 +07:00`  
HEAD: `8c49d3a2d727d86c13096bb5814095e32776fa77`

Review the narrow repair of the High finding in
`CP-A-rereview-3-bugbot-review-2026-09-24.md` against these exact hashes:

```text
backend/ingestion/parser.py 6e3305e0aecd8bfcf4d145c89ad37186cc4933f7546ebf1e9808307dba261cc4
backend/ingestion/schema.py 1e2f2d5ecfd235c419527d9cddef504bd930c40437b3c99f485c573a3fda0e5b
scripts/review_decisions.py d123909b4fe161330f84763c45592888e5a192f5569fe28fe3abb625fcdcced1
scripts/build_registry.py 0d2ad4e14415fed4e33aac26c86155c76093accee26025c73f81bb4a1a6acdff
tests/test_amendment_payload.py 149ef8adef95b71c3015366bb5ee72be971d398bb672a9a9a152fa99f926124e
tests/test_review_decisions.py 26b7266a6b43d15ae2f663c6da56f9d5c4bb05876aab03fcd8ed3113284b8a92
data/raw/official/02-2025-ND-CP-congbao.pdf e7d5d66154cd8f43c0d7ac441e312d9511cfc2dac0005e3fcebf58048a0d9072
```

## Claimed remediation to verify independently

The parser now uses the same closing-quote pattern both while parsing payloads
and while deciding whether a top-level-looking `Điều N` should remain inside
the current article. If a quoted payload closes between the most recent
structural item and the ordinary line ending in `như sau:`, amendment verbs
before that closing boundary are ignored. Only an amendment verb on the final
line itself can then retain the following `Điều N` as payload.

The new regression is
`test_closed_quoted_payload_point_cannot_trigger_later_ordinary_intro`. It
failed before repair because `body/article:2` was absent and now checks both
inline and quote-only closures while requiring that top-level article to be
preserved. Adjacent guards cover the round-2 trigger,
wrapped amendment instructions, unquoted article payloads, point-level
instructions and the earlier unnumbered instruction case.

## Builder verification

```text
Exact new regression before repair: 1 failed
New regression variants plus adjacent guards after repair: 7 passed in 0.12s
Focused parser/review suite with workspace tmp fixture: 48 passed in 0.80s
Full current suite with workspace tmp fixture: 75 passed in 8.69s
Canonical NĐ 02/2025 pages 1-9: 69 pieces, 69 unique paths, 0 duplicates,
  4 item-8 payload points
py_compile: PASS
git diff --check on changed files: PASS (line-ending warning only)
```

No corpus rebuild, registry decision, generated data update or publish was
performed. The temporary workspace-backed pytest directories created by this
run were removed.

## Required independent review

Recompute all seven hashes before review. Rerun the round-3 trigger, the
round-2 trigger, CPA-01…04 and the four original Bugbot findings. Include both
inline and quote-only payload closures, then confirm legitimate single-line,
wrapped and point-level amendment instructions still retain their payload.
Record reviewer identity/time, commands, findings and final decision in a new
review record.

The builder does not sign CP-A. P1R-04, CP-B, Gate 1 and Phase 2 remain blocked
unless this independent review returns PASS on the pinned digest.
