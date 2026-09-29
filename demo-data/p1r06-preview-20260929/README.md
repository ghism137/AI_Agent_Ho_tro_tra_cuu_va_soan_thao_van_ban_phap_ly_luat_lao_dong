# Demo data preview — 2026-09-29

Scope: source-text search, document reading and citation UI prototyping. This is a filtered derivative of historical candidate-b4031f5962906d9e, whose P1R-05 fidelity decision is preserved here. It is not a new legal acceptance decision.

Use chunks.jsonl for search; doc_id, structural_path, source_refs and content_hash identify the original text. parsed.json contains the corresponding document ASTs. sources.json provides official URLs and local source-byte hashes; raw PDFs are not bundled.

Do not infer current applicability, effective dates, consolidated law, population predicates or legal advice from this preview. P1R-06 remains FAIL — NOT SIGNED OFF. Historical sign-off wording and candidate labels apply only to their historical snapshot; they do not sign any gate for this preview.

Excluded: documents without selected official candidate sources; seven documents changed by the parser rebuild (02/2025, 32/2013, 41/2024, 45/2019, 46/2014, 74/2025, 75/2023); Law 113/2025 identity-conflict work. No pending operation proposals or materialized legal states are included.

This directory is immutable demo handoff data; ongoing data repair can continue independently. Consumers should pin this Git commit and manifest hashes. Dependencies are not a complete legal corpus; cross-references may point outside the subset.
