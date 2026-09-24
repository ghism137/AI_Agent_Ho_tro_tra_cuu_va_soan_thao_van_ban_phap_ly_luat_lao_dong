# CP-A independent re-review, round 2 — Bugbot

Status: `FAIL — NOT SIGNED OFF`  
Reviewer: Bugbot, independent review; result relayed by the user  
Reviewer file mutations: none  
Exact reviewer runtime and completion time: unavailable

This record preserves the independent result supplied by the user. It was
entered by the coordinator; the coordinator did not perform or sign the review.

## Reviewed digest and reported verification

All seven SHA-256 values in
`CP-A-rereview-2-request-2026-09-24.md` were reported to match the pinned
digest. The review also reported that the four findings from the prior Bugbot
review were closed, the focused suite passed `50 passed`, the canonical PDF
result was `69 pieces / 69 unique paths / 4 item-8 payload points`, and
`py_compile` plus `git diff --check` passed.

## Finding

**High — `backend/ingestion/parser.py:68`:**
`current_expects_amendment_payload()` searches for an amendment verb throughout
the entire current article while only requiring the final line to end in
`như sau:`. An ordinary clause can therefore cause the next `Điều N` to be
consumed as amendment payload, losing a top-level article and producing
duplicate locators without quarantine.

## Disposition

CP-A remains failed and cannot be signed off. P1R-04 has not started. CP-B is
`NOT_READY / NOT_REVIEWABLE`; Gate 1, Phase 1 closeout and Phase 2 remain
unsigned. No source file was changed in response to this report.

