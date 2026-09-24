# P1R-00 baseline and review reconciliation

Date: 2026-09-23. Task owner planned: Terra. Actual executor: Codex (`gpt-5`; reasoning effort unavailable). Status: **BLOCKED**. This task only reads inputs and creates the files in this directory plus its packet. It does not rebuild the registry or candidate, modify production data/code, publish, or make a legal acceptance decision.

## Pinned state

- Git HEAD: `8c49d3a2d727d86c13096bb5814095e32776fa77`.
- Registry: 258 sources, 61 documents, 15 coverage rows, 0 source quarantine rows, 31 verified-relation records and 15 operations. Hashes are in [scope lock](scope_lock_p1r00.json).
- Operations are 13 `pending` and 2 `blocked`; none are `verified`. This is a baseline fact, not a decision about their legal effect.
- Stored staging manifest is `candidate-3995dbe3f41d51cd` (61 documents, 20,410 chunks, 20,318 provision versions, `published=false`). Its stored code fingerprint is stale against the 23/09 review fingerprint `candidate-c350e21f2516a157`; no candidate was rebuilt to resolve that difference.
- The active pointer remains `phase1-febf5129f0e33d40`. Its file hash and the source-selection hash match the 23/09 review evidence. This is not a re-hash or acceptance of the release snapshot.

## Scope lock result

[scope_lock_p1r00.json](scope_lock_p1r00.json) pins the 61 current IDs, 15 coverage rows, as-of date and six legal groups. It deliberately does **not** claim the required 37 base-document set is known: the historical `reports/phase1-closeout/scope_lock.json` has `total_documents_count: 0`, `documents: []`, and `base_documents_37: []`. A text search of the P1R-00 inputs found statements that 37 documents were intended, but no authoritative 37-ID list.

This blocks scope-lock acceptance. The next work must recover the list from a dated, hash-pinned source or obtain a scope decision; it must not silently substitute the current 61 documents or reduce the requirement.

## Review record reconciliation

Read-only in-memory classification of `data/registry/reviews/*.json` uses current `input_hash`, source membership and decision grouping by `(subject_type, subject_id, review_type, input_sha256)`.

- Active decisions: 41, all `document/metadata`; all 41 are applicable.
- Stale or unsupported active decisions: 0.
- True duplicates: 0. Conflicts: 0. There are no active source/identity decisions; filenames beginning `identity_` contain document metadata decisions.
- Archive manifest: 61 entries, Class A 41 and Class B 20. All listed archive files exist. Existence only confirms archive completeness, not legal validity of an archived decision or its replacement.
- Applying active decisions in memory to neutral defaults produces 41 verified and 20 pending documents; the generated `documents.json` still records all 61 as verified. No registry writer was run, so this is a reconciliation finding rather than a materialized output.

The 20 pending IDs are in the 23/09 review evidence and must be handled by P1R-04 through source-grounded review decisions. The result does not create replacement decisions or change review status.

## Tests

The required full command was attempted three times, including a fresh report base temp, a fresh system base temp and pytest's default temp:

```text
venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
```

Each attempt ran 35 tests successfully and produced three setup errors for the `tmp_path` fixtures in `tests/test_amendment_payload.py`. The final attempt exited 1 because `pytest` was denied `os.scandir` access to `C:\Users\Admin\AppData\Local\Temp\pytest-of-Admin`; explicitly supplied base-temp paths instead failed during pytest session cleanup with the same `PermissionError`. This is an environment/sandbox blocker, not evidence that the three assertions fail.

The same three assertions were then executed manually against a task-owned directory with the same `ReviewDecision`, `apply_document_decisions` and `load_decisions` calls: divergent values raise `ValueError`, exact duplicates apply once, and `archive/` is skipped. Result: 3/3 PASS.

On 2026-09-24 the complete current suite was also run with an evidence pytest
plugin that changed only the `tmp_path` fixture root to a process-specific
`tmp/pytest-workspace-<pid>` directory inside the writable workspace. The
plugin SHA-256 is
`75e8359f178c597504ecb139c221a5d083167c6d36c519b938963a4fc558a82e`:

```text
$env:PYTHONPATH = (Resolve-Path -LiteralPath 'reports/phase1-closeout/repair-2026-09-23').Path
venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider -p pytest_workspace_tmp
Initial evidence run: 66 passed in 9.53s
Latest rerun after adding the second CP-A review regressions: 71 passed in 9.14s
```

The reproducible plugin is retained as
`repair-2026-09-23/pytest_workspace_tmp.py`; generated test directories were
deleted after the run. This establishes that every current test assertion
passes; it does not establish that pytest can use the sandbox-denied system
temp root without the override.

## Working-tree preservation

The task began with tracked dirty changes in bootstrap/session/workflow/AGENTS, parser/chunker, decision scripts and one locator test; it also began with untracked `.gemini/`, `scratch/create_issues.ps1`, `tests/test_amendment_payload.py` and the 23/09 review directory. Their hashes and diff scope were captured in the task packet. P1R-00 added only the new baseline directory and packet; no pre-existing change was reset, staged or modified.

## Handoff

P1R-00 remains blocked only by the missing 37-ID scope record. The product test
assertions are no longer an unresolved blocker, although the host's default
pytest temp directory is still inaccessible. Do not treat this packet as CP-A
review or Phase 1 sign-off.
