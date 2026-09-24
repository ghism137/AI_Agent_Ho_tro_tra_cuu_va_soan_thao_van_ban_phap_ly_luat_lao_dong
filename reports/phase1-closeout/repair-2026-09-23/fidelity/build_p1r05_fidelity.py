import json
import re
import os
import unicodedata
import os
from collections import defaultdict
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[4]
metadata_dir = ROOT / "reports/phase1-closeout/repair-2026-09-23/metadata"
fidelity_dir = ROOT / "reports/phase1-closeout/repair-2026-09-23/fidelity"
staging_dir = ROOT / "data/staging/phase1-candidate"
registry_dir = ROOT / "data/registry"
cleaned_dir = ROOT / "data/cleaned"
raw_dir = ROOT / "data/raw"

def content_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def file_hash(filepath):
    if not filepath.exists():
        return None
    return hashlib.sha256(filepath.read_bytes()).hexdigest()

def main():
    fidelity_dir.mkdir(parents=True, exist_ok=True)
    batch_file = metadata_dir / "batch-01.json"
    parsed_file = staging_dir / "parsed.json"
    ops_file = registry_dir / "operations.json"
    
    batch01 = json.loads(batch_file.read_text(encoding="utf-8"))
    parsed = json.loads(parsed_file.read_text(encoding="utf-8"))
    operations = json.loads(ops_file.read_text(encoding="utf-8"))
    
    report = {
        "task_id": "P1R-05",
        "batch": 1,
        "status": "BUILDER_DONE",
        "input_hashes": {
            "batch-01.json": file_hash(batch_file),
            "parsed.json": file_hash(parsed_file),
            "operations.json": file_hash(ops_file)
        },
        "documents": [],
        "cross_references": []
    }
    
    extracted_files = {}
    for f in cleaned_dir.glob("*.json"):
        try:
            ext_meta = json.loads(f.read_text(encoding="utf-8")).get("metadata", {})
            if "doc_number" in ext_meta:
                extracted_files[ext_meta["doc_number"]] = f
        except:
            pass

    chunks_list = []
    chunks_path = staging_dir / "chunks.jsonl"
    if chunks_path.exists():
        with open(chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks_list.append(json.loads(line))
        report["input_hashes"]["chunks.jsonl"] = file_hash(chunks_path)
                    
    chunks_by_doc = defaultdict(list)
    for c in chunks_list:
        chunks_by_doc[c.get("doc_id")].append(c)

    for doc in batch01["documents"]:
        doc_id = doc["doc_id"]
        doc_data = parsed.get(doc_id)
        
        doc_report = {
            "doc_id": doc_id,
            "status": "audited",
            "source_hashes": {},
            "section_index": [],
            "duplicate_structural_paths": [],
            "missing_numbering": [],
            "annex_contamination": [],
            "table_cells": [],
            "dependent_operations": [],
            "blocked_operations": [],
            "fidelity_mismatches": []
        }
        
        raw_path_str = doc.get("source", {}).get("path")
        raw_source_id = doc.get("source", {}).get("source_id")
        ext_file = None
        if raw_path_str:
            raw_file = ROOT / raw_path_str
            if raw_file.exists():
                doc_report["source_hashes"]["raw"] = file_hash(raw_file)
                
        if not doc_data:
            doc_report["status"] = "missing_in_parsed"
            report["documents"].append(doc_report)
            continue
            
        articles = doc_data.get("articles", [])
        
        path_counts = defaultdict(list)
        
        for idx, art in enumerate(articles):
            path = "/".join(art.get("structural_path", []))
            path_counts[path].append(idx)
            content = art.get("content", "")
            art_num = str(art.get("article_number"))
            
            # Record section index with source locators and section hash
            locators = [seg.get("locator") for seg in art.get("content_segments", []) if seg.get("locator")]
            doc_report["section_index"].append({
                "path": path,
                "locators": locators,
                "hash": content_hash(content)
            })
            
            # We perform fidelity checks after the loop below.

        if raw_path_str.endswith(".docx"):
            # Direct DOCX Extraction Verification (Bypass Cleaned JSON)
            try:
                import sys
                from pathlib import Path
                if str(ROOT) not in sys.path:
                    sys.path.insert(0, str(ROOT))
                from backend.ingestion.docx_extractor import extract_docx
                
                blocks = extract_docx(ROOT / raw_path_str)
                block_map = {}
                for b in blocks:
                    if b['kind'] == 'paragraph':
                        block_map[b['locator']] = unicodedata.normalize('NFC', b['text'].strip())
                    elif b['kind'] == 'table':
                        for row_idx, r in enumerate(b.get('rows', [])):
                            text = ' | '.join(r)
                            block_map[f"{b['locator']}/row:{row_idx+1}"] = unicodedata.normalize('NFC', text.strip())
                            
                for a in articles:
                    for seg in a.get("content_segments", []):
                        loc = seg.get("locator")
                        txt = unicodedata.normalize('NFC', seg.get("text", "").strip())
                        if loc not in block_map:
                            doc_report["fidelity_mismatches"].append({
                                "path": loc,
                                "reason": "missing_in_extracted"
                            })
                        else:
                            txt_clean = re.sub(r'\s+', '', txt).lower()
                            blk_clean = re.sub(r'\s+', '', block_map[loc]).lower()
                            if txt_clean != blk_clean:
                                doc_report["fidelity_mismatches"].append({
                                    "path": loc,
                                    "reason": "content_mismatch"
                                })
                            
            except Exception as e:
                doc_report["fidelity_mismatches"].append({
                    "path": raw_path_str,
                    "reason": f"missing_provenance_to_raw ({e})"
                })
        else:
            # For PDF, Verify strict parity between parsed.json and chunks.jsonl
            doc_chunks = chunks_by_doc.get(doc_id, [])
            chunk_map = {c.get("locator") or "/".join(c.get("structural_path", [])): unicodedata.normalize('NFC', c.get("content", "").strip()) for c in doc_chunks}
            
            # 1. Verify provenance refs
            for c in doc_chunks:
                refs = [ref.get("source_id") for ref in c.get("source_refs", [])]
                if raw_source_id not in refs:
                    doc_report["fidelity_mismatches"].append({
                        "path": c.get("locator", "") or "/".join(c.get("structural_path", [])),
                        "reason": "missing_provenance_to_raw"
                    })
            
            # 2. Check that every parsed article is correctly represented in chunks
            parsed_paths = set()
            for a in articles:
                path = "/".join(a.get("structural_path", []))
                parsed_paths.add(path)
                txt = unicodedata.normalize('NFC', a.get("content", "").strip())
                if path not in chunk_map:
                    doc_report["fidelity_mismatches"].append({
                        "path": path,
                        "reason": "missing_chunk_coverage"
                    })
                else:
                    txt_clean = re.sub(r'\s+', '', txt).lower()
                    chk_clean = re.sub(r'\s+', '', chunk_map[path]).lower()
                    if txt_clean != chk_clean:
                        doc_report["fidelity_mismatches"].append({
                            "path": path,
                            "reason": "content_mismatch"
                        })
            
            # 3. Check for extra/duplicate chunks
            for cp in chunk_map.keys():
                if cp not in parsed_paths:
                    doc_report["fidelity_mismatches"].append({
                        "path": cp,
                        "reason": "missing_in_parsed"
                    })
        
        for idx, art in enumerate(articles):
            path = "/".join(art.get("structural_path", []))
            content = art.get("content", "")
            
            # Check annex contamination
            if "body" in art.get("structural_path", []) and "phụ lục" in content.lower():
                if re.match(r"^Phụ lục\s+", content, re.I):
                    doc_report["annex_contamination"].append({"path": path, "excerpt": content[:50]})
                    
            # Check missing numbering
            struct_path = art.get("structural_path", [])
            if struct_path and ("item:" in struct_path[-1] or "point:" in struct_path[-1]):
                if not re.match(r"^(\d+|[a-zđ]+)[.)]", content.strip(), re.I):
                    doc_report["missing_numbering"].append({"path": path, "excerpt": content[:50].replace('\n', ' ')})
                    
        for p, idxs in path_counts.items():
            if len(idxs) > 1:
                doc_report["duplicate_structural_paths"].append({"path": p, "count": len(idxs)})
                
        # Source tables logic
        source_tables = doc_data.get("source_tables", [])
        if source_tables:
            total_cells = sum(len(t.get("cells", [])) for t in source_tables)
            doc_report["table_cells"].append({"count": total_cells, "note": f"Counted cells across {len(source_tables)} tables"})
                
        # cross reference operations
        for op in operations:
            s_clause = op.get("source_clause", "")
            t_loc = op.get("target_locator", "")
            if s_clause.startswith(doc_id) or t_loc.startswith(doc_id):
                doc_report["dependent_operations"].append(op["operation_id"])
                # check if blocked
                r_status = op.get("review_status", "").lower()
                status = op.get("status", "").lower()
                if r_status in ["pending", "unknown"] or status in ["pending", "unknown"]:
                    doc_report["blocked_operations"].append({
                        "operation_id": op["operation_id"],
                        "status": r_status or status
                    })
                    
        if doc_report["fidelity_mismatches"]:
            doc_report["status"] = "mismatched"
                
        report["documents"].append(doc_report)
        
    (fidelity_dir / "batch-01.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
