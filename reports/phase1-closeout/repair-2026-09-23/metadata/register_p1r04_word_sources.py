"""Register the six P1R-04 official Word sources without writing review decisions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
INVENTORY = ROOT / "reports/phase1-implementation/inventory.json"
SOURCES = ROOT / "data/registry/sources.json"
DOCUMENTS = ROOT / "data/registry/documents.json"
SELECTIONS = ROOT / "data/registry/source_selection.json"
MANIFEST = ROOT / "data/raw/official/p1r04_word_manifest.json"

RAW_WORD_PATHS = {
    "doc:10/2012/QH13": "data/raw/word/Bộ-luật-10-2012-QH13.docx",
    "doc:12/2012/QH13": "data/raw/word/Bộ-Luật-12-2012-QH13.docx",
    "doc:25/2008/QH12": "data/raw/word/luât-25-2008-QH12.docx",
    "doc:38/2013/QH13": "data/raw/word/Luật-38-2013-QH13.docx",
    "doc:58/2014/QH13": "data/raw/word/Luật-58-2014-QH13.docx",
    "doc:84/2015/QH13": "data/raw/word/Luật-84-2015-QH13.docx",
}

STALE_PATHS = {
    "data/raw/word/Luật-12-2012-QH13.docx",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_row(entry: dict, *, url: str | None, role: str | None) -> dict:
    return {
        "source_id": entry["source_id"],
        "path": entry["path"],
        "sha256": entry["sha256"],
        "format": entry["format"],
        "source_url": url,
        "collected_at": "2026-09-24" if url else None,
        "verification_status": "pending",
        "extraction_method": "docx_xml",
        "source_role": role,
    }


def main() -> None:
    inventory = load(INVENTORY)
    inventory_by_path = {row["path"]: row for row in inventory["sources"]}
    manifest = load(MANIFEST)
    manifest_by_doc = {f"doc:{row['document']}": row for row in manifest}
    sources = load(SOURCES)
    documents = load(DOCUMENTS)
    selections = load(SELECTIONS)
    docs_by_id = {row["doc_id"]: row for row in documents}

    managed_paths = set(STALE_PATHS)
    managed_paths.update(RAW_WORD_PATHS.values())
    managed_paths.update(row["path"] for row in manifest)
    removed_ids = {row["source_id"] for row in sources if row["path"] in managed_paths}
    sources = [row for row in sources if row["path"] not in managed_paths]
    for document in documents:
        document["source_ids"] = [sid for sid in document["source_ids"] if sid not in removed_ids]

    for doc_id, official in manifest_by_doc.items():
        official_path = official["path"]
        raw_path = RAW_WORD_PATHS[doc_id]
        official_entry = inventory_by_path[official_path]
        raw_entry = inventory_by_path[raw_path]
        for entry in (official_entry, raw_entry):
            actual = ROOT / entry["path"]
            if file_hash(actual) != entry["sha256"] or actual.stat().st_size != entry["bytes"]:
                raise ValueError(f"Inventory mismatch: {entry['path']}")
        if official_entry["sha256"] != official["sha256"] or official_entry["bytes"] != official["bytes"]:
            raise ValueError(f"Manifest mismatch: {official_path}")
        if official_entry["sha256"] != raw_entry["sha256"]:
            raise ValueError(f"Official/raw Word bytes differ for {doc_id}")

        sources.append(source_row(official_entry, url=official["url"], role="body"))
        sources.append(source_row(raw_entry, url=None, role="alternate"))
        document = docs_by_id[doc_id]
        document["source_ids"] = sorted(set(document["source_ids"] + [
            official_entry["source_id"], raw_entry["source_id"]
        ]))
        selections[doc_id] = {
            "body": official_path,
            "alternate": [raw_path],
            "reason": (
                "User-provided Word attachment from the official VBPL record is selected; "
                "the pre-existing raw Word copy is byte-identical and retained only as an alternate."
            ),
        }

    sources.sort(key=lambda row: row["source_id"])
    documents.sort(key=lambda row: row["doc_id"])
    dump(SOURCES, sources)
    dump(DOCUMENTS, documents)
    dump(SELECTIONS, selections)
    print(json.dumps({
        "registered_official_sources": len(manifest),
        "selected_documents": len(manifest),
        "registry_decisions_written": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
