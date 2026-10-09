# Demo SOURCE_ONLY — baseline 09/10/2026

This directory is derived demo data. `../p1r06-preview-20260929/` is the unchanged
snapshot from commit `75672de20c1862bf3e8ec88718833a17744789a0`.

`manifest.json` pins every preview file and `supplement.json` by SHA-256. The
search adapter refuses changed bytes. The preview supplies 29 documents and
9,990 chunks; 9,513 normative chunks with an article locator enter search.
The other 477 are excluded from search. Seven reviewed BLLĐ 2019 excerpts
cover the three BASIC demo topics. Search has 9,520 chunks total.

The seven excerpts are copied from B02-R5 (Điều 24–26), B03-R1 (Điều 27), and
B04-R1 (Điều 111, 112, 115). Each row retains the exact excerpt hash, official
source URL, source-byte hash, PDF page locator, packet manifest digest, review
digest and row ID. The reproduction command, when the separate BASIC packet
directory is available, is:

```powershell
python scripts/build_demo_supplement.py <basic-packet-directory> demo-data/source-only/supplement.json
python scripts/build_demo_manifest.py
```

Neither excerpt fidelity nor the historical preview implies current legal
effect, individual applicability, population completion or calculation
authority. The seven open legal decisions remain DEFER; no legal gold is
created here. `effective_status=unknown`, `legal_as_of_verified=false` and
`mode=SOURCE_ONLY` are intentional. Original source snapshots, approved
adapter, publisher and release gates remain outside this demo.
