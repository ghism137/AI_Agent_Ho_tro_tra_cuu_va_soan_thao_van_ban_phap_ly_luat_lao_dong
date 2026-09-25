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
    if (staging_dir / "chunks.jsonl").exists():
        with open(staging_dir / "chunks.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks_list.append(json.loads(line))
                    
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
                
        # Find extracted file by provenance (metadata doc_number)
        if doc_data and "metadata" in doc_data and "doc_number" in doc_data["metadata"]:
            parsed_doc_number = doc_data["metadata"]["doc_number"]
            if parsed_doc_number in extracted_files:
                ext_file = extracted_files[parsed_doc_number]
                doc_report["source_hashes"]["extracted"] = file_hash(ext_file)
        
        ext_data = {}
        if ext_file:
            ext_data = json.loads(ext_file.read_text(encoding="utf-8"))
            
        if not doc_data:
            doc_report["status"] = "missing_in_parsed"
            report["documents"].append(doc_report)
            continue
            
        articles = doc_data.get("articles", [])
        ext_articles = ext_data.get("articles", []) if isinstance(ext_data, dict) else []
        ext_articles_map = {str(a.get("article_number")): unicodedata.normalize('NFC', a.get("content", "")) for a in ext_articles}
        
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
            
            # Prove fidelity: normalize and check substring
            content_norm = unicodedata.normalize('NFC', content).strip()
            if ext_file:
                if art_num not in ext_articles_map:
                    if str(art_num).lower() not in ["none", ""]:
                        doc_report["fidelity_mismatches"].append({
                            "path": path,
                            "reason": "missing_in_extracted"
                        })
                else:
                    ext_content_norm = ext_articles_map[art_num]
                    if content_norm not in ext_content_norm:
                        doc_report["fidelity_mismatches"].append({
                            "path": path,
                            "reason": "content_mismatch"
                        })

        if ext_file:
            parsed_art_nums = {str(a.get("article_number")) for a in articles}
            for ext_art_num in ext_articles_map.keys():
                if ext_art_num not in parsed_art_nums and str(ext_art_num).lower() not in ["none", ""]:
                    doc_report["fidelity_mismatches"].append({
                        "path": f"extracted/article:{ext_art_num}",
                        "reason": "missing_in_parsed"
                    })
        else:
            # If no extracted file (PDFs), verify provenance by checking chunks
            for c in chunks_by_doc.get(doc_id, []):
                refs = [ref.get("source_id") for ref in c.get("source_refs", [])]
                if raw_source_id not in refs:
                    doc_report["fidelity_mismatches"].append({
                        "path": c.get("locator", ""),
                        "reason": "missing_provenance_to_raw"
                    })
            
            # Check annex contamination
            if "body" in art.get("structural_path", []) and "phß╗Ñ lß╗Ñc" in content.lower():
                if re.match(r"^Phß╗Ñ lß╗Ñc\s+", content, re.I):
                    doc_report["annex_contamination"].append({"path": path, "excerpt": content[:50]})
                    
            # Check missing numbering
            struct_path = art.get("structural_path", [])
            if struct_path and ("item:" in struct_path[-1] or "point:" in struct_path[-1]):
                if not re.match(r"^(\d+|[a-z─æ]+)[.)]", content.strip(), re.I):
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
        elif not doc_report["source_hashes"].get("extracted") and raw_path_str and not raw_path_str.endswith(".pdf"):
            doc_report["status"] = "missing_extracted"
                
        report["documents"].append(doc_report)
        
    (fidelity_dir / "batch-01.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
