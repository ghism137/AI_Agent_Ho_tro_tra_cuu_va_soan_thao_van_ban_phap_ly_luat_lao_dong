# CP-A independent Bugbot review — 2026-09-24

Status: `FAIL`  
Reviewer: Bugbot, independent review; report relayed by the user  
File mutations by reviewer: none  
Exact reviewer runtime and completion timestamp: unavailable

This record preserves the independent result supplied by the user. It was
transcribed into the repository by the repair builder; the builder did not
perform or sign this review.

## Reviewed digest

The review targeted the hashes pinned by
`CP-A-rereview-request-2026-09-23.md`, including:

```text
backend/ingestion/parser.py e4e9be6e84a0780434ac5a7afbb4ca49a03021d8058e38b53b93a79dec206400
backend/ingestion/schema.py 093b79d44259030b74e3a585a45c3a6d29ce58c0e3d5695004ac6e74673213e9
scripts/review_decisions.py d123909b4fe161330f84763c45592888e5a192f5569fe28fe3abb625fcdcced1
scripts/build_registry.py 0d2ad4e14415fed4e33aac26c86155c76093accee26025c73f81bb4a1a6acdff
tests/test_amendment_payload.py 562414f1e78e423e68820f59ef77c16cd4434a5728c0bd966aec0b6e7eb9258b
tests/test_review_decisions.py 6bdfbdf81f54c0927b28df57481a6b11442d6e4d3318035c675a49a6e487d77c
```

## Findings

1. **High — `backend/ingestion/parser.py:383`:** an unquoted payload beginning
   with `Điều N` can be intercepted as a top-level article and quarantine
   before `pending_payload` sees it.
2. **High — `backend/ingestion/parser.py:224`:** an unquoted payload can exit
   its scope early on a sequential clause containing an amendment verb,
   silently assigning an incorrect legal locator instead of quarantining the
   ambiguity.
3. **High — `backend/ingestion/schema.py:26`:** `EvidenceRef.locator` and
   `ReviewDependency.dependency_id` accept blank strings, permitting empty v2
   bindings to materialize as verified.
4. **Medium — `scripts/review_decisions.py:251`:** a rejected decision applies
   `verified_values` to a document before changing its status, allowing
   metadata from a rejected review to be written.

Reported verification: the prior CPA-01…04 regressions passed at
`36 passed, 3 deselected`; the canonical PDF produced 69 pieces and 69 unique
paths; `py_compile` and `git diff --check` passed. These checks did not negate
the four findings.

## CP-B disposition

`NOT_READY / NOT_REVIEWABLE`. Missing inputs include the request/digest,
P1R-04…07 evidence directories, the authoritative base 37-ID list and legal
sign-off. Operations remain 13 pending and 2 blocked. No Gate 1 acceptance or
Phase 2 implementation authority follows from this review.

