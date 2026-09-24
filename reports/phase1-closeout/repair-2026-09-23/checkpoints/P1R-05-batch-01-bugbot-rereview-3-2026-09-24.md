# P1R-05 batch-01 independent Bugbot re-review round 3 — 2026-09-24

Status: `FAIL — NOT SIGNED OFF`  
Reviewer: Bugbot, independent review; result relayed by Codex `/root`  
Reviewed at: `2026-09-24 23:10:12 +07:00`  
Reviewer file mutations: none  
Exact reviewer runtime: unavailable

## Verified repairs

- Three of three report-level hashes and five of five selected raw hashes match.
- Current DOCX lookup yields one extracted file per document number, but the
  extraction provenance is not yet cryptographically bound to selected raw.
- The three PDF datasets currently have path-count parity (`214/214`,
  `340/340`, `794/794`) and no bad source reference, although the builder does
  not enforce these invariants.
- Table-cell totals are correctly four and two.
- Operations pinning, blocked-operation semantics and `BUILDER_DONE` status
  remain correct.
- Two regenerations are identical; current CRLF output SHA-256 is
  `7c9ef8f9860a9843c0a7451147f487c51f739284c3c21152d4b55a0b89b8def2`.

## Blocking findings

### High — DOCX provenance remains ambiguous

At `fidelity/build_p1r05_fidelity.py:54`, extracted artifacts are indexed only
by `metadata.doc_number`. Duplicate document numbers would overwrite silently,
and extracted metadata contains no selected raw path, hash or source ID. The
current one-file result does not prove extraction from the exact official raw
selected by P1R-04.

### High — PDF coverage is observed but not enforced

At `fidelity/build_p1r05_fidelity.py:158`, the PDF branch verifies source IDs
only on chunks that exist. It does not fail on total or partial missing chunks,
does not compare raw PDF content with parsed content, and does not pin
`chunks.jsonl` in `input_hashes`. Fidelity can pass with incomplete coverage.

### High — two-way check is article-number-only

At `fidelity/build_p1r05_fidelity.py:148`, reverse comparison covers only the
set of article numbers. A missing paragraph, item or point inside an otherwise
present article is not detected.

### High — six substantive mismatches still block acceptance

`fidelity/batch-01.json` contains six real content mismatches across Articles
168, 169 and 242 of `10/2012`, and Article 8 of `12/2012`. Both documents are
correctly marked `mismatched`, so the five-item batch cannot pass.

## Decision

P1R-05 batch 1 remains failed. Bind DOCX extraction to selected raw provenance,
pin and enforce complete PDF coverage, compare structural content below the
article level, and resolve or explicitly disposition all six substantive
mismatches before another independent review. Later fidelity batches and
CP-B/Gate 1/Phase 1/Phase 2 remain blocked.
