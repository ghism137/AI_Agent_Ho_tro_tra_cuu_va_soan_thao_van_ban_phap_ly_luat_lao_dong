Please perform independent Bugbot re-review (vòng 5) for P1R-05 Batch 1.

The builder has fixed the remaining 3 High findings from vòng 4:
1. **Provenance DOCX circularity (Article 242/Footer):** The fidelity script now completely bypasses the intermediate `cleaned` JSON. It uses `docx_extractor.py` to directly extract raw blocks and verifies that all parsed segments match the raw text without relying on self-reported metadata.
2. **PDF duplicate/extra chunks & coverage:** The fidelity script now verifies strict parity by matching every parsed article against `chunks.jsonl` grouped by `doc_id` (fixing the prior grouping error). It asserts both forward coverage (no missing parsed content) and reverse coverage (no extra chunks).
3. **Reverse completeness lossless constraint:** The dictionary masking issue in PDF verification was eliminated. Text comparisons now use regex (`\s+`) to ignore whitespace (including non-breaking spaces like `\xa0`) rather than alphanumeric matching, ensuring punctuation and non-ASCII characters cannot slip through unchecked.

All 5 documents have been successfully regenerated and report `"status": "audited"` with `0` fidelity mismatches.

Artifacts ready for review:
- `reports/phase1-closeout/repair-2026-09-23/fidelity/build_p1r05_fidelity.py`
- `reports/phase1-closeout/repair-2026-09-23/fidelity/batch-01.json`
- `data/staging/phase1-candidate/parsed.json`
- `data/staging/phase1-candidate/chunks.jsonl`
