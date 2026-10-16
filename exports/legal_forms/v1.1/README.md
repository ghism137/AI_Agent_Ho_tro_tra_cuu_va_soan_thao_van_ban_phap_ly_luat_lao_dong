# Legal forms v1.1 — derived retrieval metadata

**RETRIEVAL_DATASET — CONTENT_INTEGRITY_VERIFIED / LEGAL_APPLICABILITY_UNVERIFIED**

This package supplements `../v1/`; it does not copy or change the 212 form and 131 annex source records. Ship both folders together. No embedding, crawl, re-chunking, date correction, DOCX rendering or production agent is included.

## Files and counts

- `metadata_overlay.jsonl`: 343 rows joined to v1 by `chunk_id`. `source_integrity=MATCH` is a freshly checked SHA256 of all directly referenced raw bytes; alternative DOCX files are explicitly NOT_CHECKED. `content_integrity=MATCH` checks original text hash. All rows remain `legal_metadata_status=PENDING_REVIEW`, `structural_fidelity=TEXT_ONLY`, `generation_ready=false`.
- `template_candidates.jsonl`: 208 provision-version groups: 185 source-form groups and 23 annex heading candidates. Original `content_kind` is retained. Annex headings are descriptive, not an accepted template classification; even FORM candidates require source inspection before use.
- `fragment_groups.jsonl`: 257 groups covering every input chunk exactly once, grouped by `provision_id` and `provision_version_id`. Group fields include document, full structural path and all source IDs. `part_index` is 1-based physical source order. It is not a character offset; `lossless_reassembly_verified=false` for every group. No text is concatenated or reconstructed.
- `annex_review_queue.jsonl`: 23 uncertain annex groups, excluded from the candidate index. These remain NEEDS_REVIEW; no automatic promotion to form.
- `duplicate_content_groups.jsonl`: 37 repeated hash groups across both source kinds. Safe subgroups require exact document/provision/version/release/path, dates/status and source references including locators. Equal hash alone never authorizes collapse. All original records and chunk IDs remain available.
- `docx_mapping_candidates.json`: original published registry DOCX records grouped by document, for contextual alternatives only. DIRECT means direct DOCX provenance, not verified template structure. UNVERIFIED_ALTERNATIVE means same-document registry alternatives exist; content equivalence and their raw bytes have not been checked. NONE means no DOCX alternative is listed in that registry.
- `manifest.json` pins v1 files, snapshot, code hashes, timestamp and build base. `SHA256SUMS.txt` covers every generated file except itself, including this generated README and Git attributes. Every file in this folder is generated deterministically.

## Safe usage

Join overlay rows by `chunk_id`; fetch content from the unchanged v1 JSONL. Use complete `doc_id`, `provision_id`, `provision_version_id`, `structural_path` and `source_ids` to identify candidates. The helper `select_candidates` performs exact metadata filtering; it does not understand natural-language intent or certify selection correctness. A request such as “Mẫu số 01” alone is insufficient.

`deduplicate_hits` preserves ranking and groups hits only within equal full provenance contexts. It retains all member IDs. It rejects an empty or non-list source_refs value, any non-object reference, or any reference whose source_id/locator is missing, blank/whitespace-only or not a string. Every reference is checked before a grouping key is created; missing URLs remain allowed when ID and locator are complete. Do not deduplicate distinct versions or sources by content hash. No retrieval engine or running product/index is modified.

Example from the repository root:

```python
import json
from pathlib import Path
from scripts.build_legal_forms_v11 import select_candidates

folder = Path('exports/legal_forms/v1.1')
candidates = [json.loads(line) for line in (folder / 'template_candidates.jsonl').read_text(encoding='utf-8').splitlines()]
chosen = candidates[0]  # Inspect a known registry candidate; this is not semantic selection.
matches = select_candidates(candidates, doc_id=chosen['doc_id'], provision_id=chosen['provision_id'], source_id=chosen['source_ids'][0])
assert chosen in matches
```

## Unresolved findings and review boundary

F01/F02: dates and legal status remain unreviewed. Overlay flags suspicious issuance years, repeated 2020-01-01 dates, null valid_to and distinct chunk/source verification states; it never invents a replacement date or RESOLVED label.

F03: STRUCTURAL_FIDELITY_LIMITATION persists. Tables, merges, layout and rendered DOCX equivalence remain unverified; no STRUCTURE_VERIFIED labels are emitted. Production document generation stays BLOCKED.

F04: group membership and source order are covered; lossless reassembly is not verified. F05: annex candidates and uncertainty queue are surfaced; original labels remain unchanged. F06: DOCX alternatives stay unverified. F07: safe dedup metadata/helper is provided without modifying original chunks. F08: missing URLs stay null. F09: exporter now rejects both MISSING and MISMATCH raw sources before writing output.

The original v1 manifest keeps the historical exporter fingerprint. Replaying v1 with the hardened exporter changes its exporter SHA256 only; do not overwrite that historical manifest. Use a fresh output directory for a new export.

**MANUAL_ENGINEERING_REVIEW = ACCEPT; EXP11-R01 = CLOSED**, independently reviewed at commit `f6e9023e70e282998e13bfb4d73608ad4e0e221d` on 16/10/2026. The reviewer reran 37/37 tests successfully and confirmed rejection of incomplete provenance, unchanged v1/derived data bytes, and no new P1/P2 findings. [Accepted re-review report](../reviews/EXPORT_PHASE1_V11_REREVIEW_f6e9023_20261016.md) follows the preserved [initial MODIFY review](../reviews/EXPORT_PHASE1_V11_REVIEW_4611111_20261016.md).

Owner authorized the subsequent GitHub handoff. This post-review update records that decision and refreshes generated README/manifest/checksums; engineering implementation and all six derived data files remain unchanged from the reviewed commit. Acceptance is bound to the reviewed commit above. This was direct independent review, not Bugbot: BUGBOT_REVIEW remains NOT_RUN_RUNNER_UNAVAILABLE. Engineering acceptance does not cover legal applicability, semantic template selection, DOCX structural/render fidelity or production document generation. Legal statuses remain PENDING_REVIEW, TEXT_ONLY and generation_ready=false.

## Reproduction

From the feature checkout, with the source repository holding the pinned release and raw files:

```powershell
python -X utf8 scripts/build_legal_forms_v11.py --source-repo 'C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động' --export-timestamp '2026-10-16T18:33:16+07:00' --base-commit 9bf662b99fc8219085e22aa61df44382ce52c828
$env:LEGAL_FORM_SOURCE_REPO='C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động'
python -X utf8 -m unittest discover -s tests -p 'test_legal_form*.py' -v
```

The full release and v1 checksums are validated, then 101 directly referenced raw files are hashed offline. Input pin checks run before and after writing. Existing differing output is refused. Reuse timestamp, base and code bytes for exact replay; Python 3.10+ stdlib only. Source paths resolve relative to the source repository. v1 README and FORM_CATALOG remain the original handoff docs, protected by their checksums but not regenerated here.
