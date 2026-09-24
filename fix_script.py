import json
from pathlib import Path

ROOT = Path(".")
script = ROOT / "reports/phase1-closeout/repair-2026-09-23/fidelity/build_p1r05_fidelity.py"
content = script.read_text(encoding="utf-8")

old_str = """    for doc in batch01["documents"]:
        doc_id = doc["doc_id"]
        doc_id_str = doc_id.replace("doc:", "").replace("/", "-")
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
        
        # Locate raw and extracted files from batch-01 source path
        raw_path_str = doc.get("source", {}).get("path")
        ext_file = None
        if raw_path_str:
            raw_file = ROOT / raw_path_str
            if raw_file.exists():
                doc_report["source_hashes"]["raw"] = file_hash(raw_file)
                # Extracted file typically shares the same stem, but is .json in cleaned_dir
                ext_file = cleaned_dir / (raw_file.stem + ".json")
                if ext_file.exists():
                    doc_report["source_hashes"]["extracted"] = file_hash(ext_file)
                else:
                    ext_file = None
        
        ext_data = {}
        if ext_file:
            ext_data = json.loads(ext_file.read_text(encoding="utf-8"))
            
        if not doc_data:"""

new_str = """    extracted_files = {}
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
            
        if not doc_data:"""

content = content.replace(old_str, new_str)

old_str2 = """            # Prove fidelity: normalize and check substring
            content_norm = unicodedata.normalize('NFC', content).strip()
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
                    })"""

new_str2 = """            # Prove fidelity: normalize and check substring
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
                    })"""

content = content.replace(old_str2, new_str2)

# Fix mismatched status logic to not fail PDFs
old_str3 = """        if doc_report["fidelity_mismatches"] or not doc_report["source_hashes"].get("extracted"):
            doc_report["status"] = "mismatched" if doc_report["fidelity_mismatches"] else "missing_extracted\""""

new_str3 = """        if doc_report["fidelity_mismatches"]:
            doc_report["status"] = "mismatched"
        elif not doc_report["source_hashes"].get("extracted") and raw_path_str and not raw_path_str.endswith(".pdf"):
            doc_report["status"] = "missing_extracted\""""

content = content.replace(old_str3, new_str3)

script.write_text(content, encoding="utf-8")
print("Done")
