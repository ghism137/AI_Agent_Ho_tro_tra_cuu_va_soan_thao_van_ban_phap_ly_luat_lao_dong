# P1R-05 batch-01 independent Bugbot review — 2026-09-24

Status: `FAIL — NOT SIGNED OFF`  
Reviewer: Bugbot, independent review; result relayed by Codex `/root`  
Reviewed at: `2026-09-24 15:35:33 +07:00`  
Reviewer file mutations: none  
Exact reviewer runtime: unavailable

## Verified inputs and determinism

- Both hashes pinned in `P1R-05.md` matched.
- The report contains exactly the five batch-01 document IDs.
- Independent in-memory regeneration was byte-identical to `batch-01.json`,
  SHA-256 `50eaa56bb405d02853035712285e5a234bc436404b9f90ee37acc1cdaa4727c7`.

## Blocking findings

### High — stale parsed-only audit

`fidelity/build_p1r05_fidelity.py:20` reads only the known-stale
`candidate-3995dbe3f41d51cd` `parsed.json`. The section loop around line 54
re-hashes parsed content and locators but never reads selected raw source bytes
or extracted evidence. It therefore does not prove raw-to-extracted-to-parsed
fidelity, and the zero-violation claim is unsupported.

### High — authoritative source tables ignored

At `fidelity/build_p1r05_fidelity.py:67`, the table audit searches for pipe
characters in article text and ignores `parsed[doc].source_tables`. Independent
reproduction found two tables/four cells for `doc:10/2012/QH13` and one
table/two cells for `doc:12/2012/QH13`, while the corresponding report arrays
are empty.

### High — operation dependency incomplete and unpinned

At `fidelity/build_p1r05_fidelity.py:86`, `operations.json` affects output but
is not pinned in the packet. The report retains only `operation_id`, omitting
source clause, target locator and review disposition. The operation for
`doc:10/2012/QH13` is pending, has unknown source/target hashes and a downgrade
reason, yet the document is marked audited and the packet reports no blocker.

### Medium — premature reviewed status

At `fidelity/build_p1r05_fidelity.py:26`, builder output uses
`REVIEWED_FIDELITY` before independent review, conflicting with the packet's
builder-done/reviewer-pending state.

## Decision

P1R-05 batch 1 fails review. Repair the four findings, add focused regressions
and pin every input that affects the report before requesting re-review. Do not
continue later fidelity batches or infer CP-B, Gate 1, Phase 1 or Phase 2
acceptance from this deterministic but incomplete audit.
