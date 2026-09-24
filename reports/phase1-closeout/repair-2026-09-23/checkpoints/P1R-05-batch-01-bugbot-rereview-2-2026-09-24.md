# P1R-05 batch-01 independent Bugbot re-review round 2 — 2026-09-24

Status: `FAIL — NOT SIGNED OFF`  
Reviewer: Bugbot, independent review; result relayed by Codex `/root`  
Reviewed at: `2026-09-24 22:37:22 +07:00`  
Reviewer file mutations: none  
Exact reviewer runtime: unavailable

## Verified repairs

- All three pinned report inputs match.
- All five raw paths and hashes match the exact official sources selected by
  P1R-04.
- Table-cell totals are correctly four for `doc:10/2012/QH13` and two for
  `doc:12/2012/QH13`.
- Operations pinning, blocked-operation handling and builder report status
  remain correct.

## Blocking findings

### High — extracted input is guessed, not provenance-bound

At `fidelity/build_p1r05_fidelity.py:76`, the extracted path is inferred as
`data/cleaned/<raw stem>.json`. This misses the available extracted file for
`12/2012` because its selected raw name differs, and no extracted chain exists
for the three PDF inputs. Four of five documents therefore lack a proven
raw-to-extracted-to-parsed chain.

### High — one-way substring comparison cannot prove completeness

At `fidelity/build_p1r05_fidelity.py:93`, comparison iterates only parsed nodes
and tests whether parsed content occurs in an extracted article. It cannot
detect an extracted article or paragraph omitted entirely from parsed output.
NFC normalization does not close this two-way coverage gap.

### High — no document currently passes fidelity

`fidelity/batch-01.json:$.documents[*].fidelity_mismatches` contains 1,490
mismatches: 1,485 `missing_in_extracted` and five `content_mismatch`. The five
explicit content mismatches for `doc:10/2012/QH13` concern Articles 168, 169
and 242. All five documents are correctly marked `mismatched`; none is eligible
for fidelity sign-off.

## Decision

P1R-05 batch 1 remains failed. Bind extracted artifacts through explicit
provenance, implement a two-way coverage/content comparison and resolve or
explain every remaining substantive mismatch before another independent
review. Do not continue later fidelity batches or infer CP-B, Gate 1, Phase 1
or Phase 2 acceptance.
