Please perform independent Bugbot re-review (vòng 6) for P1R-05 Batch 1.

The builder has fixed the remaining 2 High findings from vòng 5:
1. **PDF duplicate/locator checking (chunk dictionary masking):** The chunk checking logic no longer uses a dictionary mapped by locator. It now uses a `Counter` to strictly enforce that every normative segment in `parsed.json` is covered exactly ONCE by `chunks.jsonl`. Duplicates will be explicitly flagged as `duplicate_chunk_coverage`, and chunks with fake locators or incorrect source_ids are flagged as `invalid_chunk_locator` or `missing_provenance_to_raw`. Furthermore, the chunks are now verified directly against the RAW PDF using `pdf_text_extractor.py`, ensuring any mutations to the raw PDF will be correctly caught.
2. **Reverse completeness lossless constraint (DOCX gap detection):** The script now implements strict reverse completeness inside articles. For both DOCX and PDF, the script finds the minimum and maximum locator indices of an article within the raw blocks array. It then verifies that EVERY raw block falling within that bounded sequence is present in the `parsed.json` `content_segments` for that article. If a normative paragraph (e.g., `body/p:40` of Article 8) is deleted from `parsed.json`, the script will immediately flag it as `missing_in_parsed` because it physically falls between `body/p:39` and `body/p:41` in the raw document sequence.

All 5 documents have been successfully verified against the raw DOCX/PDF extractors and report `"status": "audited"` with `0` fidelity mismatches.

Artifacts ready for review:
- `reports/phase1-closeout/repair-2026-09-23/fidelity/build_p1r05_fidelity.py`
- `reports/phase1-closeout/repair-2026-09-23/fidelity/batch-01.json`
- `data/staging/phase1-candidate/parsed.json`
- `data/staging/phase1-candidate/chunks.jsonl`
