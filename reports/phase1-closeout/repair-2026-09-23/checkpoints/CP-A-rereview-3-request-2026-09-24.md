# CP-A independent re-review request, round 3 — 2026-09-24

Status: `READY_FOR_INDEPENDENT_REVIEW — NOT SIGNED OFF`  
Builder: Codex `/root`, runtime model ID `gpt-5`; reasoning effort unavailable  
Prepared at: `2026-09-24 08:09:18 +07:00`  
HEAD: `8c49d3a2d727d86c13096bb5814095e32776fa77`

Review the narrow repair of the High finding in
`CP-A-rereview-2-bugbot-review-2026-09-24.md` against these exact hashes:

```text
backend/ingestion/parser.py 1a2ec461ddb269bea32432f99033218d662a1ad4f9a31e1729f4ec10db080efd
backend/ingestion/schema.py 1e2f2d5ecfd235c419527d9cddef504bd930c40437b3c99f485c573a3fda0e5b
scripts/review_decisions.py d123909b4fe161330f84763c45592888e5a192f5569fe28fe3abb625fcdcced1
scripts/build_registry.py 0d2ad4e14415fed4e33aac26c86155c76093accee26025c73f81bb4a1a6acdff
tests/test_amendment_payload.py ed2f4bc121ce05db3067a1ac4d77b3c2db86e6a6bf906e91cdad5002fef064ef
tests/test_review_decisions.py 26b7266a6b43d15ae2f663c6da56f9d5c4bb05876aab03fcd8ed3113284b8a92
data/raw/official/02-2025-ND-CP-congbao.pdf e7d5d66154cd8f43c0d7ac441e312d9511cfc2dac0005e3fcebf58048a0d9072
```

## Claimed remediation to verify independently

`current_expects_amendment_payload()` no longer searches the entire current
article for an amendment verb. When the last line ends in `như sau:`, the verb
must occur in the most recent numbered clause/point; if there is no such item,
it must occur on the last line itself. This keeps an ordinary clause from
inheriting an amendment verb from a preceding clause and consuming the next
top-level `Điều N`.

The new regression is
`test_ordinary_intro_after_prior_amendment_clause_keeps_next_top_level_article`.
It failed before the repair because `body/article:2` was absent; it now requires
that top-level path and confirms that no `amendment_payload` path is created.

## Builder verification

```text
Exact new regression before repair: 1 failed
Exact new regression after repair plus adjacent invariants: 4 passed in 0.13s
Focused parser/review suite with workspace tmp fixture: 46 passed in 0.80s
Full current suite with workspace tmp fixture: 73 passed in 9.74s
Canonical NĐ 02/2025 pages 1-9: 69 pieces, 69 unique paths, 0 duplicates,
  4 item-8 payload points
py_compile: PASS
git diff --check on changed files: PASS (line-ending warning only)
```

No corpus rebuild, registry decision, generated data update or publish was
performed. The temporary workspace-backed pytest directories created by this
run were removed.

## Required independent review

Recompute all seven hashes before review. Rerun the new trigger, the earlier
CPA-01…04 invariants and the four findings closed in round 2. Confirm that
legitimate single-line and multi-line amendment instructions still admit their
payload while amendment verbs in prior structural items cannot affect the next
top-level article. Record reviewer identity/time, commands, findings and final
decision in a new review record.

The builder does not sign CP-A. P1R-04, CP-B, Gate 1 and Phase 2 remain blocked
unless this independent review returns PASS on the pinned digest.
