# P1R-05 batch-01 independent Bugbot re-review — 2026-09-24

Status: `FAIL — NOT SIGNED OFF`  
Reviewer: Bugbot, independent review; result relayed by Codex `/root`  
Reviewed at: `2026-09-24 15:44:57 +07:00`  
Reviewer file mutations: none  
Exact reviewer runtime: unavailable

## Verified repairs

- All three report-level input hashes match.
- Two generations are byte-identical; output SHA-256 is
  `c33702864cf30a480823cc9ad25f8b417ab1f3af9d77ec5cc09982b5aeab0deb`.
- `operations.json` is pinned and the pending operation for
  `doc:10/2012/QH13` appears in `blocked_operations`.
- Report status is correctly `BUILDER_DONE`.

The prior operation-pinning and premature-status findings are closed.

## Blocking findings

### High — wrong/unproven source chain

At `fidelity/build_p1r05_fidelity.py:74`, the script selects the first filename
match returned by `os.walk`. For `10/2012` and `12/2012` it pins `manual_md`
files instead of the official sources selected in P1R-04. The three PDF
documents `113/2025`, `124/2025` and `142/2025` have no extracted input but are
still marked audited. The script hashes raw input without comparing raw content
to extracted content, so raw-to-extracted-to-parsed fidelity remains unproven.

### High — mismatches do not fail the audit

`fidelity/batch-01.json:$.documents[*].fidelity_mismatches` contains 1,162
mismatches: 1,033 for `10/2012` and 129 for `12/2012`. Despite this, the
documents remain `audited` and the packet claims fidelity is proved. Articles
absent from extracted data are also skipped at
`fidelity/build_p1r05_fidelity.py:113`.

### High — table count is table count, not cell count

At `fidelity/build_p1r05_fidelity.py:132`, `table_cells.count` uses
`len(source_tables)`. That reports two and one, while the authoritative data
contains four cells for `doc:10/2012/QH13` and two cells for
`doc:12/2012/QH13`.

## Decision

P1R-05 batch 1 remains failed. Repair the three High findings and add focused
regressions before another independent re-review. Do not continue later
fidelity batches or infer CP-B, Gate 1, Phase 1 or Phase 2 acceptance.
