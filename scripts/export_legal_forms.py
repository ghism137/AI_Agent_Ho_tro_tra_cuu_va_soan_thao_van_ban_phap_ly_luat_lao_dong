"""Offline, byte-preserving export from a hash-verified published Phase 1 snapshot."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

CHUNKS = "data/staging/phase1-candidate/chunks.jsonl"
SOURCES = "data/registry/sources.json"
DOCUMENTS = "data/registry/documents.json"
REQUIRED = {
    "chunk_id", "content_kind", "content", "content_hash", "doc_id", "doc_number",
    "structural_path", "source_refs", "provision_id", "provision_version_id",
    "release_id", "verification_status", "valid_from", "valid_to", "is_fragment",
}
LIMITATIONS = [
    "STRUCTURAL_FIDELITY_LIMITATION: retrieval plain text does not retain DOCX table merges, widths, styles, pagination or exact layout; no exact DOCX reconstruction claim.",
    "Snapshot verification_status and dates are preserved, not revalidated legal applicability at document-generation time. Current Phase 1 closeout is OPEN / NOT SIGNED OFF.",
    "Published container ID and embedded candidate release_id differ; both are recorded without rewriting source records.",
    "Unique forms means unique provision_id, not deduplicated legal templates; full-document and standalone sources can repeat content.",
    "Fragments have no explicit fragment index or character offsets in this snapshot; source line order is retained, and exact lossless reassembly is not certified.",
    "Missing URLs remain null. Non-DOCX sources do not have a certified exact DOCX counterpart; document-registry alternatives are contextual only.",
    "Annex categories are descriptive text evidence, not legal review; ambiguous or mixed annexes remain NEEDS_REVIEW.",
    "Raw corpus and snapshot data are external, ignored inputs: repository commit alone does not identify their bytes; use pinned SHA256 values.",
    "Date metadata contains repeated 2020-01-01 values and issuance years inconsistent with document-number years; retained unchanged and flagged for separate legal metadata review.",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def bad_constant(value):
        raise ValueError(f"Non-JSON constant: {value}")

    return json.loads(data, object_pairs_hook=pairs, parse_constant=bad_constant)


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes root: {relative}")
    return path


def read_snapshot(repo):
    repo = Path(repo).resolve()
    pointer_path = repo / "data/active_release.json"
    pointer_bytes = pointer_path.read_bytes()
    pointer = strict_json(pointer_bytes)
    release = inside(repo, pointer["path"])
    if release != (repo / "data/releases" / pointer["release_id"]).resolve():
        raise ValueError("Pointer is not a published release path")
    manifest_bytes = (release / "manifest.json").read_bytes()
    if sha(manifest_bytes) != pointer["manifest_sha256"]:
        raise ValueError("Active manifest SHA256 mismatch")
    manifest = strict_json(manifest_bytes)
    if manifest["release_id"] != pointer["release_id"] or manifest.get("published") is not True:
        raise ValueError("Not a matching published release")
    pins = {pointer_path: sha(pointer_bytes), release / "manifest.json": sha(manifest_bytes)}
    for relative, expected in manifest["snapshot_file_sha256"].items():
        path = inside(release, relative)
        actual = sha(path.read_bytes())
        if actual != expected:
            raise ValueError(f"Snapshot SHA256 mismatch: {relative}")
        pins[path] = actual
    for relative in (CHUNKS, SOURCES, DOCUMENTS):
        if relative not in manifest["snapshot_file_sha256"]:
            raise ValueError(f"Unpinned snapshot input: {relative}")
    # Recheck each consumed input against its pin, including concurrent changes.
    def consume(relative):
        data = (release / relative).read_bytes()
        if sha(data) != pins[release / relative]:
            raise ValueError(f"Input changed during read: {relative}")
        return data
    registry = strict_json(consume(SOURCES))
    documents = strict_json(consume(DOCUMENTS))
    sources = {s["source_id"]: s for s in registry}
    docs = {d["doc_id"]: d for d in documents}
    if len(sources) != len(registry) or len(docs) != len(documents):
        raise ValueError("Duplicate registry identities")
    records = []
    ids = set()
    for number, line in enumerate(consume(CHUNKS).splitlines(keepends=True), 1):
        record = strict_json(line.decode("utf-8"))
        if not isinstance(record, dict) or REQUIRED - record.keys():
            raise ValueError(f"Missing chunk schema at line {number}")
        if record.get("schema_version") != 2:
            raise ValueError(f"Unexpected schema at line {number}")
        accepted_ids = {pointer["release_id"], pointer["release_id"].replace("phase1-", "candidate-", 1)}
        if record["release_id"] not in accepted_ids:
            raise ValueError(f"Unrelated embedded release_id at line {number}")
        if record["content_kind"] not in ("form", "annex", "normative"):
            raise ValueError(f"Unexpected content kind at line {number}")
        if record["chunk_id"] in ids:
            raise ValueError(f"Duplicate chunk_id at line {number}")
        ids.add(record["chunk_id"])
        if sha(record["content"].encode("utf-8")) != record["content_hash"]:
            raise ValueError(f"Content hash mismatch at line {number}")
        if record["content_length"] != len(record["content"]):
            raise ValueError(f"Content length mismatch at line {number}")
        if not record["source_refs"] or record["doc_id"] not in docs:
            raise ValueError(f"Missing provenance at line {number}")
        for ref in record["source_refs"]:
            if ref["source_id"] not in sources:
                raise ValueError(f"Unmapped source_id at line {number}")
            if ref["source_id"] not in docs[record["doc_id"]]["source_ids"]:
                raise ValueError(f"Source/document mapping mismatch at line {number}")
        # Keep physical JSON line bytes and source order, including source whitespace.
        records.append((number, line, record))
    if len(records) != manifest["chunks"]:
        raise ValueError("Manifest chunk count mismatch")
    return repo, release, pointer, manifest, sources, docs, records, pins


def unchanged(pins):
    for path, expected in pins.items():
        if sha(path.read_bytes()) != expected:
            raise ValueError(f"Protected source changed: {path}")


def stats(records, sources):
    refs = {r["source_id"] for _, _, c in records for r in c["source_refs"]}
    return {
        "chunks": len(records),
        "unique_provision_ids": len({c["provision_id"] for _, _, c in records}),
        "unique_source_ids": len(refs),
        "unique_doc_ids": len({c["doc_id"] for _, _, c in records}),
        "fragment_chunks": sum(c["is_fragment"] for _, _, c in records),
        "source_formats": dict(sorted(Counter(sources[s]["format"] for s in refs).items())),
    }


def annex_category(chunks):
    # Only explicit opening headings; do not infer legal meaning from a stray keyword.
    opening = chunks[0][2]["content"].splitlines()[:5]
    for text in opening:
        upper = text.upper()
        if upper.startswith("MẪU CÁC VĂN BẢN"):
            return "NEEDS_REVIEW", text + " (collection/index of templates; not established as one form)"
        if upper.startswith("MẪU ") and "MẪU SỐ" not in upper:
            return "FORM", text
        if upper.startswith("DANH MỤC ĐỊA BÀN ÁP DỤNG"):
            return "APPLICATION_LIST", text
        if upper.startswith("DANH MỤC "):
            return "CATALOG", text
        if upper.startswith(("LỘ TRÌNH TUỔI NGHỈ HƯU", "TUỔI NGHỈ HƯU THẤP NHẤT", "CÔNG VIỆC KHAI THÁC THAN")):
            return "OTHER_NORMATIVE_OR_REFERENCE", text
    return "NEEDS_REVIEW", "Opening does not establish a single unambiguous category; may include form index or mixed contents."


def make_audit(repo, sources, records, pins):
    selected = [row for row in records if row[2]["content_kind"] in ("form", "annex")]
    used = sorted({r["source_id"] for _, _, c in selected for r in c["source_refs"]})
    raw_checks = []
    for sid in used:
        source = sources[sid]
        path = inside(repo, source["path"])
        actual = sha(path.read_bytes()) if path.is_file() else None
        status = "MATCH" if actual == source["sha256"] else ("MISSING" if actual is None else "MISMATCH")
        raw_checks.append({"source_id": sid, "path": source["path"], "expected_sha256": source["sha256"], "actual_sha256": actual, "status": status})
        if status == "MISMATCH":
            raise ValueError(f"Referenced raw source hash mismatch: {sid}")
        if status == "MATCH":
            pins[path] = actual
    groups = defaultdict(list)
    for row in selected:
        groups[row[2]["provision_id"]].append(row)
    inventory = []
    for pid, rows in sorted(groups.items()):
        c = rows[0][2]
        entry = {
            "provision_id": pid, "doc_id": c["doc_id"], "content_kind": c["content_kind"],
            "structural_path": c["structural_path"], "chunk_ids_in_source_order": [r[2]["chunk_id"] for r in rows],
            "source_line_numbers": [r[0] for r in rows], "heading_preview": c["content"][:240],
            "source_ids": sorted({r["source_id"] for _, _, chunk in rows for r in chunk["source_refs"]}),
            "has_fragments": any(r[2]["is_fragment"] for r in rows),
        }
        if c["content_kind"] == "annex":
            entry["category"], entry["category_evidence"] = annex_category(rows)
            entry["classification_scope"] = "Descriptive heading inspection only; no legal acceptance"
        inventory.append(entry)
    # Sample only referenced form DOCX files with table locators, largest/fragment first.
    candidates = []
    seen = set()
    form_rows = [r for r in selected if r[2]["content_kind"] == "form"]
    for row in sorted(form_rows, key=lambda r: (-r[2]["is_fragment"], -len(r[2]["content"]), r[0])):
        c = row[2]
        for ref in c["source_refs"]:
            sid = ref["source_id"]
            if sid not in seen and sources[sid]["format"] == "docx" and "table:" in ref.get("locator", ""):
                candidates.append((row, sid))
                seen.add(sid)
                break
        if len(candidates) == 3:
            break
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    samples = []
    for (line, _, c), sid in candidates:
        path = inside(repo, sources[sid]["path"])
        sample = {"chunk_id": c["chunk_id"], "source_id": sid, "source_line": line, "is_fragment": c["is_fragment"], "source_path": sources[sid]["path"]}
        if path.is_file():
            with zipfile.ZipFile(path) as archive:
                xml = ET.fromstring(archive.read("word/document.xml"))
            sample.update({"docx_tables": len(xml.findall(".//w:tbl", ns)), "docx_rows": len(xml.findall(".//w:tr", ns)), "grid_spans": len(xml.findall(".//w:gridSpan", ns)), "vertical_merges": len(xml.findall(".//w:vMerge", ns)), "text_pipe_count": c["content"].count("|"), "finding": "STRUCTURAL_FIDELITY_LIMITATION"})
        else:
            sample["finding"] = "SOURCE_MISSING_NEEDS_REVIEW"
        samples.append(sample)
    duplicate_content = defaultdict(list)
    for _, _, c in form_rows:
        duplicate_content[c["content_hash"]].append(c["chunk_id"])
    issues = {}
    for kind in ("form", "annex"):
        rows = [r for r in selected if r[2]["content_kind"] == kind]
        issues[kind] = {
            "chunks_without_ref_url": [c["chunk_id"] for _, _, c in rows if not any(r.get("source_url") for r in c["source_refs"])],
            "chunks_without_registry_url": [c["chunk_id"] for _, _, c in rows if not any(sources[r["source_id"]].get("source_url") for r in c["source_refs"])],
            "chunks_without_direct_docx": [c["chunk_id"] for _, _, c in rows if not any(sources[r["source_id"]]["format"] == "docx" for r in c["source_refs"])],
            "chunks_missing_valid_from": [c["chunk_id"] for _, _, c in rows if not c["valid_from"]],
            "chunks_missing_structural_path": [c["chunk_id"] for _, _, c in rows if not c["structural_path"]],
            "chunks_with_empty_ref_locator": [c["chunk_id"] for _, _, c in rows if any(not r.get("locator") for r in c["source_refs"])],
            "null_valid_to_count": sum(c["valid_to"] is None for _, _, c in rows),
            "date_distribution": dict(sorted(Counter(c["valid_from"] for _, _, c in rows).items())),
            "verification_status_distribution": dict(sorted(Counter(c["verification_status"] for _, _, c in rows).items())),
            "issued_year_differs_from_doc_number_year": [c["chunk_id"] for _, _, c in rows if c.get("issued_date") and (match := re.search(r"/(\d{4})/", c["doc_number"])) and c["issued_date"][:4] != match.group(1)],
        }
    return {
        "audit_scope": "Offline integrity/provenance/export only; no legal reacceptance",
        "snapshot_files_verified": len(pins) - 2 - sum(r["status"] == "MATCH" for r in raw_checks),
        "source_content_kind_counts": dict(sorted(Counter(c["content_kind"] for _, _, c in records).items())),
        "embedded_release_ids": sorted({c["release_id"] for _, _, c in records}),
        "raw_source_checks": raw_checks, "metadata_gaps": issues,
        "provision_inventory": inventory, "table_samples": samples,
        "duplicate_form_content_hash_groups": [ids for ids in duplicate_content.values() if len(ids) > 1],
        "annex_category_provision_counts": dict(sorted(Counter(e["category"] for e in inventory if e["content_kind"] == "annex").items())),
        "data_limitations": LIMITATIONS,
    }


def export(source_repo, output_dir, export_timestamp, code_repo=None, source_commit=None, exporter_base_commit=None):
    stamp = datetime.fromisoformat(export_timestamp.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Export timestamp must have a timezone")
    repo, release, pointer, manifest, sources, docs, records, pins = read_snapshot(source_repo)
    out = Path(output_dir).resolve()
    if any(out.is_relative_to(repo / name) for name in ("data", ".git")):
        raise ValueError("Output must not be inside source data or Git metadata")
    code_repo = Path(code_repo or Path(__file__).resolve().parents[1])
    def git_commit(path, revision=None):
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "--verify", "--end-of-options", (revision or "HEAD") + "^{commit}"], text=True).strip()
    products = {}
    counts = {}
    for kind in ("form", "annex"):
        rows = [row for row in records if row[2]["content_kind"] == kind]
        products[f"{kind}_chunks.jsonl"] = b"".join(line for _, line, _ in rows)
        counts[kind] = stats(rows, sources)
    audit = make_audit(repo, sources, records, pins)
    products["audit.json"] = json_bytes(audit)
    used = {r["source_id"] for _, _, c in records if c["content_kind"] in ("form", "annex") for r in c["source_refs"]}
    products["source_registry.json"] = json_bytes([sources[sid] for sid in sorted(used)])
    doc_ids = {c["doc_id"] for _, _, c in records if c["content_kind"] in ("form", "annex")}
    products["document_registry.json"] = json_bytes([docs[did] for did in sorted(doc_ids)])
    output_manifest = {
        "export_schema_version": "legal_forms.v1", "chunk_schema_version": 2,
        "source_release_id": pointer["release_id"], "embedded_chunk_release_ids": audit["embedded_release_ids"],
        "source_manifest_sha256": pointer["manifest_sha256"], "source_chunk_file": CHUNKS,
        "source_chunk_file_sha256": manifest["snapshot_file_sha256"][CHUNKS],
        "source_registry_sha256": manifest["snapshot_file_sha256"][SOURCES],
        "source_document_registry_sha256": manifest["snapshot_file_sha256"][DOCUMENTS],
        "source_pointer_sha256": pins[repo / "data/active_release.json"],
        "source_repository_commit_sha": git_commit(repo, source_commit), "exporter_base_commit_sha": git_commit(code_repo, exporter_base_commit),
        "exporter_sha256": sha(Path(__file__).read_bytes()),
        "export_timestamp": export_timestamp, "order": "Original physical source line order; original record bytes retained",
        "totals": counts, "total_exported_chunks": sum(c["chunks"] for c in counts.values()),
        "unique_provision_ids": len({c["provision_id"] for _, _, c in records if c["content_kind"] in ("form", "annex")}),
        "unique_source_ids": len(used),
        "files": {name: {"sha256": sha(data), "bytes": len(data)} for name, data in sorted(products.items())},
        "data_limitations": LIMITATIONS,
    }
    products["manifest.json"] = json_bytes(output_manifest)
    # No source writes; reject differing existing destinations before creating any file.
    for name, data in products.items():
        path = out / name
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"Refusing to overwrite differing export: {path}")
    unchanged(pins)
    out.mkdir(parents=True, exist_ok=True)
    for name, data in products.items():
        path = out / name
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(data)
    unchanged(pins)
    return output_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "exports/legal_forms/v1")
    parser.add_argument("--export-timestamp", required=True, help="Pinned ISO8601 timestamp with timezone; reuse for deterministic replay")
    parser.add_argument("--source-commit", help="Historical source commit for replay after HEAD moves; must resolve to an existing commit")
    parser.add_argument("--exporter-base-commit", help="Historical exporter base commit for replay after HEAD moves")
    args = parser.parse_args()
    result = export(args.source_repo, args.output_dir, args.export_timestamp, source_commit=args.source_commit, exporter_base_commit=args.exporter_base_commit)
    print(json.dumps({"source_release_id": result["source_release_id"], "totals": result["totals"], "files": result["files"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
