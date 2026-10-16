"""Build offline v1.1 overlays and candidate metadata without modifying v1 chunks."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_legal_forms as original

LABEL = "RETRIEVAL_DATASET — CONTENT_INTEGRITY_VERIFIED / LEGAL_APPLICABILITY_UNVERIFIED"
DEFAULT_BASE = "9bf662b99fc8219085e22aa61df44382ce52c828"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def jsonl(rows):
    return b"".join((canonical(row) + "\n").encode("utf-8") for row in rows)


def source_ids(chunk):
    return sorted({ref["source_id"] for ref in chunk["source_refs"]})


def duplicate_context(chunk):
    """Conservative equality: never merge different sources, locators or versions."""
    required = original.REQUIRED | {"issued_date"}
    if required - chunk.keys():
        raise ValueError("Incomplete chunk cannot be deduplicated")
    refs = chunk["source_refs"]
    if not isinstance(refs, list) or not refs:
        raise ValueError("Deduplication requires a nonempty source_refs list")
    for ref in refs:
        if not isinstance(ref, dict) or any(
            not isinstance(ref.get(field), str) or not ref[field].strip()
            for field in ("source_id", "locator")
        ):
            raise ValueError("Deduplication requires nonblank string source_id and locator in every source reference")
    return canonical({
        key: chunk[key] for key in (
            "content_hash", "doc_id", "provision_id", "provision_version_id", "release_id",
            "structural_path", "content_kind", "valid_from", "valid_to", "issued_date", "verification_status",
        )
    }) + canonical(sorted(refs, key=canonical))


def deduplicate_hits(chunks):
    """Preserve hit ranking and all chunk IDs; collapse only equal full contexts."""
    groups = {}
    for chunk in chunks:
        if original.sha(chunk["content"].encode("utf-8")) != chunk["content_hash"]:
            raise ValueError("Cannot deduplicate a corrupt content hash")
        key = duplicate_context(chunk)
        if key not in groups:
            groups[key] = {"representative": chunk, "chunk_ids": []}
        if chunk["chunk_id"] not in groups[key]["chunk_ids"]:
            groups[key]["chunk_ids"].append(chunk["chunk_id"])
    return list(groups.values())


def select_candidates(candidates, *, doc_id, provision_id=None, structural_path=None, source_id=None):
    """Exact metadata lookup only; no semantic or legal template selection claim."""
    if not doc_id or (provision_id is None and structural_path is None):
        raise ValueError("Specify document and provision_id or full structural_path")
    return [row for row in candidates if row["doc_id"] == doc_id
            and (provision_id is None or row["provision_id"] == provision_id)
            and (structural_path is None or row["structural_path"] == list(structural_path))
            and (source_id is None or source_id in row["source_ids"])]


def verified_v1(package):
    package = Path(package).resolve()
    sums = (package / "SHA256SUMS.txt").read_bytes()
    pins = {package / "SHA256SUMS.txt": original.sha(sums)}
    names = set()
    for line in sums.decode("utf-8").splitlines():
        expected, name = line.split("  ", 1)
        if name in names or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("Invalid or duplicate v1 checksum entry")
        names.add(name)
        path = original.inside(package, name)
        if original.sha(path.read_bytes()) != expected:
            raise ValueError(f"v1 package checksum mismatch: {name}")
        pins[path] = expected
    required = {"manifest.json", "form_chunks.jsonl", "annex_chunks.jsonl", "source_registry.json", "document_registry.json", "audit.json", "README.md", "FORM_CATALOG.md", ".gitattributes"}
    if not required.issubset(names):
        raise ValueError("Incomplete v1 package checksums")
    manifest = original.strict_json((package / "manifest.json").read_bytes())
    for name, info in manifest["files"].items():
        path = original.inside(package, name)
        if path not in pins or pins[path] != info["sha256"] or path.stat().st_size != info["bytes"]:
            raise ValueError(f"v1 manifest/checksums mismatch: {name}")
    return manifest, pins


def derive(records, sources, docs):
    selected = [row for row in records if row[2]["content_kind"] in ("form", "annex")]
    by_version = defaultdict(list)
    for row in selected:
        by_version[(row[2]["provision_id"], row[2]["provision_version_id"])].append(row)
    overlays, candidates, fragments, review_queue = [], [], [], []
    docx_candidates = {}
    for did in sorted({c["doc_id"] for _, _, c in selected}):
        docx_candidates[did] = [sources[sid] for sid in sorted(docs[did]["source_ids"]) if sources[sid]["format"] == "docx"]
    categories = {}
    for key, rows in by_version.items():
        c = rows[0][2]
        categories[key] = original.annex_category(rows) if c["content_kind"] == "annex" else ("SOURCE_FORM", "Original content_kind=form")
    for line, _, chunk in selected:
        key = (chunk["provision_id"], chunk["provision_version_id"])
        category, evidence = categories[key]
        sids = source_ids(chunk)
        direct = any(sources[sid]["format"] == "docx" for sid in sids)
        alternatives = [s["source_id"] for s in docx_candidates[chunk["doc_id"]] if s["source_id"] not in sids] if not direct else []
        reasons = ["LEGAL_APPLICABILITY_NOT_REVIEWED", "CHUNK_AND_SOURCE_STATUS_ARE_DISTINCT"]
        year = re.search(r"/(\d{4})/", chunk["doc_number"])
        if year and chunk.get("issued_date") and year.group(1) != chunk["issued_date"][:4]:
            reasons.append("ISSUED_YEAR_DIFFERS_FROM_DOC_NUMBER")
        if chunk["valid_from"] == "2020-01-01":
            reasons.append("REPEATED_BASELINE_VALID_FROM_REQUIRES_REVIEW")
        if not chunk["valid_from"]:
            reasons.append("MISSING_VALID_FROM")
        if chunk["valid_to"] is None:
            reasons.append("NULL_VALID_TO_NOT_PROOF_OF_CURRENT_EFFECT")
        kind = "FORM" if chunk["content_kind"] == "form" else ("ANNEX_FORM_CANDIDATE" if category == "FORM" else "OTHER")
        overlays.append({
            "chunk_id": chunk["chunk_id"], "source_line_number": line,
            "source_integrity": "MATCH", "source_integrity_scope": "Direct source_refs raw bytes; not alternative DOCX mappings",
            "content_integrity": "MATCH", "legal_metadata_status": "PENDING_REVIEW",
            "legal_metadata_reasons": reasons,
            "source_verification_statuses": {sid: sources[sid]["verification_status"] for sid in sids},
            "original_chunk_verification_status": chunk["verification_status"],
            "template_candidate_type": kind, "annex_descriptive_category": category,
            "docx_mapping_status": "DIRECT" if direct else ("UNVERIFIED_ALTERNATIVE" if alternatives else "NONE"),
            "docx_alternative_source_ids": alternatives,
            "docx_alternative_integrity": "NOT_CHECKED" if alternatives else "NOT_APPLICABLE",
            "structural_fidelity": "TEXT_ONLY", "generation_ready": False,
        })
    for (pid, version), rows in by_version.items():
        first = rows[0][2]
        if len({canonical([c["doc_id"], c["structural_path"], c["content_kind"]]) for _, _, c in rows}) != 1:
            raise ValueError(f"Inconsistent structure in provision version: {version}")
        sids = sorted({sid for _, _, c in rows for sid in source_ids(c)})
        identity = [first["doc_id"], pid, version, first["structural_path"], sids]
        gid = "template:" + original.sha(canonical(identity).encode("utf-8"))
        category, evidence = categories[(pid, version)]
        parts = [{"chunk_id": c["chunk_id"], "part_index": i, "source_line_number": line, "is_fragment": c["is_fragment"], "content_hash": c["content_hash"], "source_ids": source_ids(c)} for i, (line, _, c) in enumerate(rows, 1)]
        group = {
            "group_id": gid, "doc_id": first["doc_id"], "doc_number": first["doc_number"],
            "provision_id": pid, "provision_version_id": version, "structural_path": first["structural_path"],
            "source_ids": sids, "content_kind": first["content_kind"], "parts": parts,
            "part_order_semantics": "1-based physical source snapshot order; not character offsets",
            "lossless_reassembly_verified": False, "legal_metadata_status": "PENDING_REVIEW",
            "structural_fidelity": "TEXT_ONLY", "generation_ready": False,
        }
        fragments.append(group)
        if first["content_kind"] == "form" or category == "FORM":
            candidates.append({**group,
                "template_candidate_type": "FORM" if first["content_kind"] == "form" else "ANNEX_FORM_CANDIDATE",
                "classification_evidence": evidence, "annex_descriptive_category": category,
                "selection_status": "CANDIDATE_ONLY_REQUIRES_SOURCE_AND_LEGAL_REVIEW",
            })
        elif category == "NEEDS_REVIEW":
            review_queue.append({**group, "classification_evidence": evidence, "review_status": "NEEDS_REVIEW", "excluded_from_candidate_index": True})
    by_hash = defaultdict(list)
    for _, _, c in selected:
        by_hash[c["content_hash"]].append(c)
    duplicates = []
    for content_hash, chunks in sorted(by_hash.items()):
        if len(chunks) > 1:
            duplicates.append({"content_hash": content_hash, "chunk_ids": [c["chunk_id"] for c in chunks],
                "safe_context_groups": [g["chunk_ids"] for g in deduplicate_hits(chunks)],
                "cross_context_collapse_allowed": False})
    return {
        "metadata_overlay.jsonl": jsonl(overlays), "template_candidates.jsonl": jsonl(candidates),
        "fragment_groups.jsonl": jsonl(fragments), "duplicate_content_groups.jsonl": jsonl(duplicates),
        "annex_review_queue.jsonl": jsonl(review_queue),
        "docx_mapping_candidates.json": original.json_bytes({"mapping_verified": False, "alternative_source_integrity": "NOT_CHECKED", "documents": docx_candidates}),
    }, overlays, candidates, fragments, review_queue, duplicates


def build(source_repo, v1_dir, output_dir, export_timestamp, base_commit=DEFAULT_BASE):
    stamp = datetime.fromisoformat(export_timestamp.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Export timestamp requires timezone")
    v1 = Path(v1_dir).resolve()
    out = Path(output_dir).resolve()
    repo = Path(source_repo).resolve()
    code_repo = Path(__file__).resolve().parents[1]
    resolved_base = subprocess.check_output(["git", "-C", str(code_repo), "rev-parse", "--verify", "--end-of-options", base_commit + "^{commit}"], text=True).strip()
    if resolved_base != base_commit:
        raise ValueError("Build base must be a full, existing commit SHA")
    if any(out.is_relative_to(p) or p.is_relative_to(out) for p in (v1, repo / "data", repo / ".git")):
        raise ValueError("Output overlaps immutable input or source data/Git metadata")
    v1_manifest, pins = verified_v1(v1)
    _, release, pointer, manifest, sources, docs, records, snapshot_pins = original.read_snapshot(repo)
    pins.update(snapshot_pins)
    if pointer["release_id"] != v1_manifest["source_release_id"] or pointer["manifest_sha256"] != v1_manifest["source_manifest_sha256"] or manifest["snapshot_file_sha256"][original.CHUNKS] != v1_manifest["source_chunk_file_sha256"]:
        raise ValueError("Active snapshot does not match pinned v1 release")
    for kind in ("form", "annex"):
        if (v1 / f"{kind}_chunks.jsonl").read_bytes() != b"".join(line for _, line, c in records if c["content_kind"] == kind):
            raise ValueError("v1 JSONL is not an exact filter of the published snapshot")
    for name, full in (("source_registry.json", sources), ("document_registry.json", docs)):
        field = "source_id" if name.startswith("source") else "doc_id"
        for row in original.strict_json((v1 / name).read_bytes()):
            if row != full[row[field]]:
                raise ValueError(f"v1 registry record differs from published source: {name}")
    audit = original.make_audit(repo, sources, records, pins)  # fail closed on every directly referenced raw source
    products, overlays, candidates, groups, queue, duplicates = derive(records, sources, docs)
    counts = {
        "overlay_chunks": len(overlays), "template_candidates": len(candidates),
        "source_form_candidates": sum(c["content_kind"] == "form" for c in candidates),
        "annex_form_candidates": sum(c["content_kind"] == "annex" for c in candidates),
        "fragment_groups": len(groups), "annex_needs_review_groups": len(queue),
        "duplicate_content_hash_groups_all_kinds": len(duplicates),
        "direct_raw_sources_verified": len(audit["raw_source_checks"]),
        "docx_mapping_statuses": dict(sorted(Counter(c["docx_mapping_status"] for c in overlays).items())),
    }
    products[".gitattributes"] = b"* -text\n"
    products["README.md"] = (f'''# Legal forms v1.1 — derived retrieval metadata

**{LABEL}**

This package supplements `../v1/`; it does not copy or change the 212 form and 131 annex source records. Ship both folders together. No embedding, crawl, re-chunking, date correction, DOCX rendering or production agent is included.

## Files and counts

- `metadata_overlay.jsonl`: {len(overlays)} rows joined to v1 by `chunk_id`. `source_integrity=MATCH` is a freshly checked SHA256 of all directly referenced raw bytes; alternative DOCX files are explicitly NOT_CHECKED. `content_integrity=MATCH` checks original text hash. All rows remain `legal_metadata_status=PENDING_REVIEW`, `structural_fidelity=TEXT_ONLY`, `generation_ready=false`.
- `template_candidates.jsonl`: {len(candidates)} provision-version groups: {counts['source_form_candidates']} source-form groups and {counts['annex_form_candidates']} annex heading candidates. Original `content_kind` is retained. Annex headings are descriptive, not an accepted template classification; even FORM candidates require source inspection before use.
- `fragment_groups.jsonl`: {len(groups)} groups covering every input chunk exactly once, grouped by `provision_id` and `provision_version_id`. Group fields include document, full structural path and all source IDs. `part_index` is 1-based physical source order. It is not a character offset; `lossless_reassembly_verified=false` for every group. No text is concatenated or reconstructed.
- `annex_review_queue.jsonl`: {len(queue)} uncertain annex groups, excluded from the candidate index. These remain NEEDS_REVIEW; no automatic promotion to form.
- `duplicate_content_groups.jsonl`: {len(duplicates)} repeated hash groups across both source kinds. Safe subgroups require exact document/provision/version/release/path, dates/status and source references including locators. Equal hash alone never authorizes collapse. All original records and chunk IDs remain available.
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

Engineering tests do not constitute independent review, legal applicability approval, semantic template-selection acceptance or DOCX structural fidelity acceptance. Direct independent review of commit 4611111680835bf8eb8264a7afe6369aa7fb9ff6 returned MODIFY for EXP11-R01 (incomplete provenance allowed to collapse). The repaired helper rejects those inputs; its exact new commit awaits independent re-review before any owner merge. The requested Bugbot-specific runner remains unavailable; the direct review is not described as Bugbot and the repair is not self-signed off.

## Reproduction

From the feature checkout, with the source repository holding the pinned release and raw files:

```powershell
python -X utf8 scripts/build_legal_forms_v11.py --source-repo 'C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động' --export-timestamp '{export_timestamp}' --base-commit {base_commit}
$env:LEGAL_FORM_SOURCE_REPO='C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động'
python -X utf8 -m unittest discover -s tests -p 'test_legal_form*.py' -v
```

The full release and v1 checksums are validated, then {counts['direct_raw_sources_verified']} directly referenced raw files are hashed offline. Input pin checks run before and after writing. Existing differing output is refused. Reuse timestamp, base and code bytes for exact replay; Python 3.10+ stdlib only. Source paths resolve relative to the source repository. v1 README and FORM_CATALOG remain the original handoff docs, protected by their checksums but not regenerated here.
''').encode("utf-8")
    pins[Path(__file__).resolve()] = original.sha(Path(__file__).read_bytes())
    pins[Path(original.__file__).resolve()] = original.sha(Path(original.__file__).read_bytes())
    output_manifest = {
        "schema_version": "legal_forms.v1.1", "dataset_label": LABEL,
        "source_release_id": pointer["release_id"], "source_manifest_sha256": pointer["manifest_sha256"],
        "source_chunks_sha256": manifest["snapshot_file_sha256"][original.CHUNKS],
        "source_registry_sha256": manifest["snapshot_file_sha256"][original.SOURCES],
        "source_document_registry_sha256": manifest["snapshot_file_sha256"][original.DOCUMENTS],
        "v1_file_sha256": {p.relative_to(v1).as_posix(): h for p, h in pins.items() if p.is_relative_to(v1)},
        "export_timestamp": export_timestamp, "build_base_commit": base_commit,
        "code_sha256": {p.name: pins[p] for p in (Path(__file__).resolve(), Path(original.__file__).resolve())},
        "counts": counts, "legal_metadata_status": "PENDING_REVIEW", "structural_fidelity": "TEXT_ONLY",
        "independent_review_status": "MANUAL_REVIEW_MODIFY_FIX_AWAITING_REREVIEW",
        "manual_review": {"reviewed_commit": "4611111680835bf8eb8264a7afe6369aa7fb9ff6", "decision": "MODIFY", "finding": "EXP11-R01", "repair_status": "BUILDER_FIXED_AWAITING_REREVIEW"},
        "bugbot_review_status": "NOT_RUN_RUNNER_UNAVAILABLE",
        "automated_legal_document_generation_production": "BLOCKED",
        "files": {name: {"sha256": original.sha(data), "bytes": len(data)} for name, data in sorted(products.items())},
    }
    products["manifest.json"] = original.json_bytes(output_manifest)
    products["SHA256SUMS.txt"] = "".join(original.sha(data) + "  " + name + "\n" for name, data in sorted(products.items())).encode("utf-8")
    for name, data in products.items():
        path = out / name
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"Refusing to overwrite differing v1.1 artifact: {path}")
    original.unchanged(pins)
    out.mkdir(parents=True, exist_ok=True)
    for name, data in products.items():
        path = out / name
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(data)
    original.unchanged(pins)
    return output_manifest


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--v1-dir", type=Path, default=root / "exports/legal_forms/v1")
    parser.add_argument("--output-dir", type=Path, default=root / "exports/legal_forms/v1.1")
    parser.add_argument("--export-timestamp", required=True)
    parser.add_argument("--base-commit", default=DEFAULT_BASE)
    args = parser.parse_args()
    result = build(args.source_repo, args.v1_dir, args.output_dir, args.export_timestamp, args.base_commit)
    print(json.dumps(result["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
