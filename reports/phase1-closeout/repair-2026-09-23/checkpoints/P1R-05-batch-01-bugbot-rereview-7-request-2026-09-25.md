Please perform independent Bugbot re-review (vòng 7) for P1R-05 Batch 1.

The builder has fixed the remaining 4 High findings from vòng 6:
1. **Reverse completeness**: Replaced the flawed `min_idx/max_idx` gap detection with a rigorous, authoritative check against `chunks.jsonl` (which covers both PDF and DOCX). The fidelity script now extracts all expected normative locators from `chunks.jsonl` (filtering for `content_kind == "normative"`) and asserts that every single one is present in `parsed.json`. This perfectly catches boundary segment deletions (like `body/p:38` or `body/p:40`), as well as missing single-segment articles.
2. **PDF provenance**: In addition to validating multiset locators, the fidelity script now reconstructs the expected raw text for EVERY chunk using `extract_docx` / `extract_pdf_text` based on the chunk's `source_refs`. It then asserts that `chunk["content"]` is physically identical (ignoring whitespace) to the reconstructed raw string. This ensures that any `source_refs` locator swapping is immediately flagged as a `chunk_content_mismatch`. It also verifies that `doc.get("source", {}).get("source_sha256")` precisely matches `file_hash(raw_file)`.
3. **Structural audit**: Deleted the redundant second iteration over `doc_data["articles"]` which caused `section_index` and `path_counts` to artificially double. Structural paths are now correctly counted once per article.
4. **Counter không lọc normative chunks**: Specifically added `if c.get("content_kind") == "normative":` before incrementing the `chunk_locator_counts`, so valid heading chunks no longer produce false positive duplicates or false missing expectations.

All 5 documents have been successfully verified and report `"status": "audited"` with `0` fidelity mismatches.

Artifacts ready for review:
- `reports/phase1-closeout/repair-2026-09-23/fidelity/build_p1r05_fidelity.py`
- `reports/phase1-closeout/repair-2026-09-23/fidelity/batch-01.json`
- `data/staging/phase1-candidate/parsed.json`
- `data/staging/phase1-candidate/chunks.jsonl`
