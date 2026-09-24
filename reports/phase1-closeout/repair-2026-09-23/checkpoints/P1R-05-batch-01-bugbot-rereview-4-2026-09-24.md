# P1R-05 batch-01 — independent Bugbot re-review round 4

Date: 2026-09-24  
Scope: P1R-05 fidelity Batch 1 only  
Decision: `FAIL — NOT SIGNED OFF`

## Findings

| Severity | Location | Finding |
|---|---|---|
| High | `fidelity/build_p1r05_fidelity.py:89-105`; `data/cleaned/Bộ-luật-10-2012-QH13.json:19-20,1470-1473` | DOCX provenance remains circular. The builder trusts `source_id` / `source_path` fields added to mutable cleaned JSON and does not independently derive or validate cleaned content from the selected raw bytes. Article 242 contains an injected `\n \| CHỦ TỊCH...` sequence absent from the official DOCX paragraph stream, while cleaned and parsed share the altered text. |
| High | `fidelity/build_p1r05_fidelity.py:181-199` | PDF fidelity proves path presence and self-declared source ID only. Set comparison hides duplicate chunks, extra paths are ignored, and chunk content/locators are not compared with parsed or raw PDF content. |
| High | `fidelity/build_p1r05_fidelity.py:123,158-180` | The reverse completeness check is not lossless: article-number dictionary collapse can hide duplicates, and leftover content fails only when it contains ASCII letters/digits, allowing punctuation-only or non-ASCII-only legal content loss. |

## Verified closed

- Four report-level input hashes and five selected raw hashes recompute.
- `chunks.jsonl` is pinned; the current PDF data has path-count parity with no
  present duplicate or extra paths.
- Repairs for Articles 168/169 and Article 8 match official DOCX text.
- Table-cell accounting, operation blocking and builder-only status are correct.
- Two read-only regenerations produced identical output.
- Reviewer modified no files.

## Boundary

This decision applies only to P1R-05 Batch 1. Later fidelity batches remain
blocked. It does not sign CP-B, Gate 1, Phase 1 or Phase 2, and it authorizes no
registry decision, rebuild or publication.
