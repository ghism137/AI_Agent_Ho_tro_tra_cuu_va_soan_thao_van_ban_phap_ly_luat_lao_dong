# Phase 1 repair execution status — 2026-09-23

Phase 1 remains `ACTIVE/OPEN`. Phase 2 remains `DESIGN_ONLY`.

- P1R-00: blocked; baseline complete and all 75 current test assertions pass,
  but the authoritative 37-ID scope list is missing.
- P1R-01: reviewed under CP-A round 4; PASS on the pinned digest.
- P1R-02: reviewed under CP-A round 4; PASS on the pinned digest.
- P1R-03: reviewed under CP-A round 4; PASS on the pinned digest.
- P1R-04: REVIEWED / SOURCE-EVIDENCE PASS. Independent review accepted all 20
  proposals and five refreshed packet digests; zero records remain blocked. No
  registry review decision was written.
- P1R-05: batch-01 re-review round 6 ready. PDF chunks validation now uses a Counter to explicitly flag duplicates, missing locators, and directly verifies against `extract_pdf_text` instead of merely comparing two generated JSON files. Reverse completeness for both DOCX and PDF is enforced by checking bounded sequences of locators, ensuring no internal article paragraphs can be dropped without failing the fidelity audit. All 5 documents are audited with 0 mismatches.
- P1R-06: blocked by incomplete source/fidelity evidence for each legal group.
- P1R-07: blocked by P1R-04/05/06 and CP-B.
- P1R-08: fixture implementation complete; actual-operation validation blocked
  by P1R-06 and CP-B.
- P1R-09: blocked by CP-B and completion of P1R-08 on actual operations.
- P1R-10: blocked by P1R-04…09 and the 37-ID scope lock.
- P1R-11: blocked by P1R-09 and CP-C.
- P1R-12: blocked by P1R-11, CP-C and CP-D.

Current technical verification:

```text
75 passed in 8.69s (workspace-backed tmp_path evidence fixture)
48 focused parser/review tests passed in 0.80s
canonical PDF pages 1-9: 69 pieces / 69 unique paths / 4 item-8 payload points
py_compile: PASS
git diff --check: PASS (line-ending warnings only)
generated registry/staging/releases/pointer diff: none
P1R-04 packets: 4 x 5 documents; 20 proposals / 0 blocked pending
P1R-04 deterministic rebuild: PASS; registry decisions written: 0
P1R-04 source-byte hash verification: PASS
focused registry/review tests: 21 passed; stale-candidate lineage test deselected
```

P1R-00 records both the default system-temp ACL failure and the successful run
of every test assertion using a workspace-backed evidence fixture. The plugin
is retained beside the baseline and generated test directories were removed.
This test result does not replace source/legal review.

Independent Bugbot CP-A re-review round 4 confirmed all seven pinned hashes,
reported no findings and returned `PASS — SIGNED OFF`. Independent P1R-04
source review accepted the original 14 proposals, and supplemental independent
review accepted the remaining six plus all refreshed packet hashes. P1R-04 is
signed off at source-evidence level for 20/20 proposals. Later cards remain
governed by their per-document dependencies. This does not sign CP-B, Gate 1,
Phase 1 closeout or Phase 2.
The existing staging candidate still references five superseded Word source
IDs and was not mutated; it remains stale until the later gated rebuild.
