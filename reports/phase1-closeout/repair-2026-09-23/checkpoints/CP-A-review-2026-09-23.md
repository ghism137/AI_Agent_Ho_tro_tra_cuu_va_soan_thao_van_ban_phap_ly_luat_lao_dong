# CP-A independent review - 2026-09-23

Status: `FAIL`  
Reviewer: Codex `/root`; runtime model ID and reasoning effort unavailable  
Reviewed at: `2026-09-23 16:07:01 +07:00`  
HEAD: `8c49d3a2d727d86c13096bb5814095e32776fa77`

## Scope and pinned inputs

Reviewed the exact dirty inputs recorded by P1R-01, P1R-02 and P1R-03. Current
hashes matched the packets:

```text
backend/ingestion/parser.py 6e295e713334fecc63fecd99dadd7d417c90f284b0694d018622b8e63928b66e
tests/test_amendment_payload.py f6ec88d87fcb8f596fb0010817f8820fe501a82dbf2d934c99069884f78d3ebe
backend/ingestion/schema.py ab6062cc275dff508c792ca6508ab20db0b7bb161edc8668da4daf07e235f619
scripts/review_decisions.py 31256001714e01dfa412a7a13405af00917fdc9ea9d7c98af3276a2c5e588543
scripts/build_registry.py 0a4d2c9a08bf8a93f5ea0099d3d522e49cad5fcbe0349dc80c02b53d457b6d86
scripts/retired_auto_metadata_review.py 255d2055ba3eb85d9df2966bf7c28e3ac7ddcf26f813422ac29a553fbf5a814a
tests/test_review_decisions.py c1008a1e610e7558b1f2a0c843467549b29dd641861698f1e0451e4bbff571e4
data/raw/official/02-2025-ND-CP-congbao.pdf e7d5d66154cd8f43c0d7ac441e312d9511cfc2dac0005e3fcebf58048a0d9072
```

The nine canonical PDF pages were rendered and visually inspected, then the
same page interval was extracted and parsed in memory. The canonical document
produced 69 pieces and 69 unique paths. Item 8 was correctly represented as
the instruction plus four paths under
`body/article:1/item:8/amendment_payload/point:{a,b,c,d}`. Closing quote plus
sentence punctuation in the canonical source was retained correctly. This
limited source result does not override the findings below.

## Blocking findings

### CPA-01 - High - Inner amendment verb exits a quoted payload early

Trigger: a quoted replacement article contains a later clause whose text begins
with the next sequential number and an amendment verb, while the closing quote
is on a following line.

At `backend/ingestion/parser.py:219-234`, the state machine treats that clause as
the next outer amendment item without first proving that the quoted payload has
closed. Reproduction:

```text
1. Sửa đổi Điều 14 như sau:
“Điều 14. Tên
1. Nội dung một.
2. Sửa đổi kỹ thuật.
Phần còn lại.”
```

Actual: clause 2 and the closing payload text become
`body/article:1/item:2`. Expected: they remain under
`body/article:1/item:1/amendment_payload/article:14/item:2` until the outer quote
closes. This changes legal locators and can bind an operation to the wrong
instruction. It also leaves the explicit P1R-01 `inner amendment verb`
acceptance case untested.

### CPA-02 - High - Unknown payload start silently creates a duplicate path

At `backend/ingestion/parser.py:146-204`, an unrecognized line after a valid
`như sau:` instruction cancels `pending_payload` and falls back to the current
instruction path. A plain quoted single-line replacement therefore does not
enter `amendment_payload` and is not quarantined.

Reproduction:

```text
1. Sửa đổi nội dung như sau:
“Nội dung thay thế.”
```

Actual: two pieces are emitted with the same
`body/article:1/item:1` path, one for the instruction and one for the quoted
replacement. Expected: a supported payload path, or fail-closed quarantine when
the structure is genuinely ambiguous. Duplicate structural identities can
overwrite each other in path-indexed consumers.

### CPA-03 - High - V2 fingerprint closure accepts missing sources and missing dependencies

`scripts/review_decisions.py:31-40` silently omits subject source IDs that are
absent from the supplied source map. `backend/ingestion/schema.py:72-85` permits
a verified v2 metadata/fidelity decision with no dependency. A reproduction
using `source_ids=["src:a", "src:missing"]`, one available evidence source, and
`dependencies=[]` materialized the document as `verified`.

Expected: every source named by the subject must be present and hash-bound, and
the P1R-03 dependency requirement must fail closed. In addition,
`scripts/review_decisions.py:111-113` compares both `source_sha256` and
`full_content_sha256` to the same registry byte hash, so the declared full
content binding is not independently checked.

### CPA-04 - High - Production registry cannot apply any v2 decision

`scripts/build_registry.py:138-140` calls the three decision applicators without
`dependency_fingerprints` or `evidence_locator_fingerprints`. Because every v2
decision has typed evidence, `_matches()` rejects it when the locator map is
absent. The direct reproduction remained `pending` under the same call shape
used by the registry builder, while the focused unit test only passes because
it injects both maps manually.

This behavior is safely closed but incomplete: after CP-A, P1R-04 cannot create
v2 decisions that the production registry can materialize. The runtime binding
maps and their canonical construction must be wired and tested before bulk
decisions are authored.

## Checks and retest

- Suggested pytest command: exit 1 with `28 passed, 3 errors`; all three errors
  are the known sandbox `tmp_path` permission failure, not assertion failures.
- Same suite excluding those three temp-fixture tests: exit 0,
  `28 passed, 3 deselected in 0.64s`.
- Independent direct equivalents: true duplicates applied; divergent document
  values raised `ValueError`; archive subdirectory was excluded and only one
  root decision loaded.
- `py_compile` for schema, parser and decision/registry scripts: exit 0.
- `git diff --check`: exit 0; only CRLF conversion warnings were printed.
- Canonical PDF parse: 69 pieces, 69 unique paths; item 8 and source closing
  punctuation matched the rendered pages.

## Decision and required retest

CP-A remains `FAIL`. Do not start P1R-04 or claim CP-B readiness. Fix CPA-01
through CPA-04, add focused regressions for both parser reproductions and the
production v2 binding path, then re-run CP-A on new exact hashes. This review
does not sign legal fidelity, operation semantics, CP-B, or final acceptance.
