# P1R-04 independent source review — 2026-09-24

Status: `PARTIAL ACCEPTANCE — BLOCKED_MISSING_OFFICIAL_SOURCES`  
Reviewer: Bugbot, independent review; result relayed by Codex `/root`  
Reviewed at: `2026-09-24 09:18:55 +07:00`  
Reviewer file mutations: none  
Exact reviewer runtime: unavailable

## Scope and digest

The reviewer checked `P1R-04.md`, `metadata/evidence-index.json`, all four
five-document batches, their pinned digests, and the referenced registered
source bytes and locators. The 20 unique document IDs match the pending list
pinned on 2026-09-23. No evidence or digest mismatch was found.

## Accepted scope

All 14 source-backed proposals are independently acceptable at the
source-evidence level. The reviewer recomputed and matched identity, title,
issued date, general valid-from date, registered-source binding, source-byte
SHA-256, full-content hash, exact locator text/hash and subject fingerprint.

This acceptance is not a materializable registry decision. A later v2 verified
decision still requires an actual reviewer identity, typed dependencies and a
fresh dependency-bound `input_fingerprint`.

## Fail-closed records

The following six records correctly retain `proposed_values: null` and have no
selected/registered usable official source:

- `batch-01.json` `$.documents[0]`: `doc:10/2012/QH13`
- `batch-01.json` `$.documents[2]`: `doc:12/2012/QH13`
- `batch-02.json` `$.documents[0]`: `doc:25/2008/QH12`
- `batch-02.json` `$.documents[4]`: `doc:38/2013/QH13`
- `batch-03.json` `$.documents[2]`: `doc:58/2014/QH13`
- `batch-04.json` `$.documents[2]`: `doc:84/2015/QH13`

## Decision

P1R-04 is partially accepted for the 14 proposals and remains blocked for the
six records above. A builder must obtain, register and select usable official
source bytes, then prepare new proposals for independent review. No registry
decision, source selection, staging, release, operation, coverage or active
pointer change was accepted or performed. CP-B, Gate 1, Phase 1 and Phase 2
remain unsigned.
