# CP-A independent review request

Status: `SUPERSEDED` — two independent reviews failed; current fixes are pinned
in `CP-A-rereview-2-request-2026-09-24.md`.

Review the exact working-tree inputs recorded by packets P1R-01, P1R-02 and
P1R-03. The current HEAD is `8c49d3a2d727d86c13096bb5814095e32776fa77`;
the packet hashes bind the dirty files.

The reviewer must independently check:

1. canonical Nghị định 02/2025/NĐ-CP pages 1–9 against the new instruction and
   `amendment_payload` paths, including item 8 and closing quote punctuation;
2. that changed paths invalidate every dependent locator/review/operation;
3. true duplicate versus conflict behavior for source and document decisions;
4. version-2 fingerprint closure across subject, source bytes, final locator
   content and named dependencies;
5. separation of proposed/verified values and the rule that metadata cannot
   verify coverage.

Suggested independent commands:

```text
venv/Scripts/python.exe -m pytest tests/test_parser.py tests/test_amendment_payload.py tests/test_review_decisions.py -q -p no:cacheprovider
venv/Scripts/python.exe -m py_compile backend/ingestion/schema.py backend/ingestion/parser.py scripts/review_decisions.py scripts/build_registry.py
git diff --check
```

Record actual reviewer identity/time, file hashes, findings and retest result.
Do not sign legal fidelity, operation semantics, CP-B or final acceptance from
these unit tests.
