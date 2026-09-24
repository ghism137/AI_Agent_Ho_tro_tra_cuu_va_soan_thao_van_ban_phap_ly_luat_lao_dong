# P1R-01 amendment path map

Input pinned: `data/raw/official/02-2025-ND-CP-congbao.pdf`, SHA-256
`e7d5d66154cd8f43c0d7ac441e312d9511cfc2dac0005e3fcebf58048a0d9072`.

The parser now keeps the amendment instruction and replacement payload in
separate source namespaces. The instruction path remains addressable, while
quoted or structurally introduced replacement text is nested below
`amendment_payload`.

| Previous interpretation | New source path | Disposition |
| --- | --- | --- |
| payload clause reused `body/article:1/item:N` and could collide with its instruction | `body/article:1/item:N/amendment_payload/article:X/item:Y` | invalidate path-bound review/operation |
| payload point treated as an ordinary point of the instruction item | `body/article:1/item:N/amendment_payload/point:x` | invalidate path-bound review/operation |
| point-level instruction lost its point prefix | `body/article:1/item:N/point:x/amendment_payload/item:Y` | invalidate path-bound review/operation |

For canonical Nghị định 02/2025/NĐ-CP pages 1–9, item 8 now produces:

```text
body/article:1/item:8
body/article:1/item:8/amendment_payload/point:a
body/article:1/item:8/amendment_payload/point:b
body/article:1/item:8/amendment_payload/point:c
body/article:1/item:8/amendment_payload/point:d
```

Consumers requiring revalidation: `operations.json` source clauses and payload
refs, fidelity decisions, locator-bound legal/effect decisions, parsed/chunk
identities and any evidence samples that cite the old structural path. The map
does not authorize changing `op-nd02-1-1` to verified.
