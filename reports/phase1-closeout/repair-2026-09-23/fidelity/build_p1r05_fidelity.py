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
    import sys
    if len(sys.argv) > 1:
        batch_num = int(sys.argv[1])
    else:
        raise ValueError("Must provide batch number as first argument, e.g. '1' or '2'")
        
    batch_name = f"batch-{batch_num:02d}.json"
    
    fidelity_dir.mkdir(parents=True, exist_ok=True)
    batch_file = metadata_dir / batch_name
    parsed_file = staging_dir / "parsed.json"
    ops_file = registry_dir / "operations.json"
    
    batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
    parsed = json.loads(parsed_file.read_text(encoding="utf-8"))
    operations = json.loads(ops_file.read_text(encoding="utf-8"))
    
    report = {
        "task_id": "P1R-05",
        "batch": batch_num,
        "status": "BUILDER_DONE",
        "input_hashes": {
            batch_name: file_hash(batch_file),
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

    for doc in batch_data["documents"]:
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
        
        # Build path_counts and section_index EXACTLY ONCE
        for idx, art in enumerate(articles):
            path = "/".join(art.get("structural_path", []))
            path_counts[path].append(idx)
            
            art_content = art.get("content", "")
            locators = [seg.get("locator") for seg in art.get("content_segments", []) if seg.get("locator")]
            doc_report["section_index"].append({
                "path": path,
                "locators": locators,
                "hash": content_hash(art_content)
            })

        # Unified fidelity check for DOCX and PDF using chunks.jsonl
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
            
        # 0. Hash validation
        if "raw" in doc_report["source_hashes"]:
            if doc_report["source_hashes"]["raw"] != doc.get("source", {}).get("source_sha256"):
                doc_report["fidelity_mismatches"].append({
                    "path": raw_path_str,
                    "reason": "raw_hash_mismatch"
                })

        raw_blocks = []
        if raw_path_str.endswith(".docx"):
            from backend.ingestion.docx_extractor import extract_docx
            raw_blocks = extract_docx(ROOT / raw_path_str)
        elif raw_path_str.endswith(".html"):
            from backend.ingestion.html_extractor import extract_government_html
            raw_blocks = extract_government_html(ROOT / raw_path_str)
        elif raw_path_str.endswith(".pdf"):
            import pymupdf
            from backend.ingestion.pdf_text_extractor import extract_pdf_text
            pdf_path = ROOT / raw_path_str
            doc_len = len(pymupdf.open(pdf_path))
            first_page = 1
            last_page = doc_len
            pdf_page_bounds = {
                "doc:113/2025/QH15": (93, 107),
                "doc:124/2025/QH15": (84, 108),
                "doc:142/2025/QH15": (41, 100),
                "doc:30/2023/QH15": (1, 17),
                "doc:32/2013/QH13": (1, 11),
                "doc:35/2018/QH14": (1, 77),
                "doc:46/2014/QH13": (1, 14),
                "doc:68/2020/QH14": (1, 27),
                "doc:71/2025/QH15": (39, 69),
                "doc:73/2025/QH15": (57, 75),
                "doc:74/2025/QH15": (29, 56),
                "doc:84/2025/QH15": (4, 44),
                "doc:97/2015/QH13": (1, 30),
            }
            if doc_id in pdf_page_bounds:
                first_page, last_page = pdf_page_bounds[doc_id]
            else:
                raise AssertionError(f"Missing hardcoded page bounds for PDF: {doc_id}")
                
            raw_blocks = extract_pdf_text(pdf_path, first_page=first_page, last_page=last_page)
            
        if raw_blocks:
            block_map = {}
            raw_locators = []
            for b in raw_blocks:
                if b['kind'] == 'paragraph':
                    block_map[b['locator']] = unicodedata.normalize('NFC', b['text'].strip())
                    raw_locators.append(b['locator'])
                elif b['kind'] == 'table':
                    for row_idx, r in enumerate(b.get('rows', [])):
                        text = ' | '.join(r)
                        loc = f"{b['locator']}/row:{row_idx+1}"
                        block_map[loc] = unicodedata.normalize('NFC', text.strip())
                        raw_locators.append(loc)

            # Extract parsed locators maintaining order
            parsed_locs = []
            for art in articles:
                for seg in art.get("content_segments", []):
                    loc = seg.get("locator")
                    if loc:
                        parsed_locs.append(loc)

            # 1. Forward Completeness (Parsed <-> Raw) & Strict Ordering
            last_raw_idx = -1
            seen_parsed = set()
            for art in articles:
                for seg in art.get("content_segments", []):
                    loc = seg.get("locator")
                    if not loc: continue
                    txt = unicodedata.normalize('NFC', seg.get("text", "").strip())
                    
                    if loc not in block_map:
                        doc_report["fidelity_mismatches"].append({
                            "path": loc,
                            "reason": "missing_provenance_to_raw"
                        })
                    else:
                        txt_clean = re.sub(r'\s+', '', txt).lower()
                        blk_clean = re.sub(r'\s+', '', block_map[loc]).lower()
                        if txt_clean != blk_clean:
                            doc_report["fidelity_mismatches"].append({
                                "path": loc,
                                "reason": "content_mismatch"
                            })
                        
                        # Strict order checking & Duplicate locator checking
                        curr_raw_idx = raw_locators.index(loc)
                        if curr_raw_idx <= last_raw_idx:
                            doc_report["fidelity_mismatches"].append({
                                "path": loc,
                                "reason": "out_of_order"
                            })
                        last_raw_idx = curr_raw_idx
                        
                    if loc in seen_parsed:
                        doc_report["fidelity_mismatches"].append({
                            "path": loc,
                            "reason": "duplicate_parsed_locator"
                        })
                    seen_parsed.add(loc)

            # 2. Provenance via chunks.jsonl
            doc_chunks = chunks_by_doc.get(doc_id, [])
            from collections import Counter
            chunk_locator_counts = Counter()
            
            for c in doc_chunks:
                # Validate chunk content matches raw text exactly (Provenance)
                chunk_text = unicodedata.normalize('NFC', c.get("content", "").strip())
                refs = c.get("source_refs", [])
                raw_text_parts = []
                is_norm = (c.get("content_kind") == "normative")
                
                for ref in refs:
                    loc = ref.get("locator")
                    src = ref.get("source_id")
                    
                    if src != raw_source_id:
                        doc_report["fidelity_mismatches"].append({
                            "path": loc or "unknown",
                            "reason": "missing_provenance_to_raw"
                        })
                        
                    if loc:
                        if is_norm:
                            chunk_locator_counts[loc] += 1
                            
                        if loc not in block_map:
                            doc_report["fidelity_mismatches"].append({
                                "path": loc,
                                "reason": "invalid_chunk_locator"
                            })
                        else:
                            raw_text_parts.append(block_map[loc])

                # Verify chunk content matches the sequence of its refs
                if raw_text_parts:
                    raw_combined_clean = re.sub(r'\s+', '', "".join(raw_text_parts)).lower()
                    chunk_clean = re.sub(r'\s+', '', chunk_text).lower()
                    if chunk_clean != raw_combined_clean:
                        doc_report["fidelity_mismatches"].append({
                            "path": c.get("locator", "chunk"),
                            "reason": "chunk_content_mismatch"
                        })
                        
            # 3. Verify exactly 1-to-1 mapping with normative chunks
            from collections import Counter
            parsed_locs_counts = Counter(parsed_locs)
            
            for loc, count in parsed_locs_counts.items():
                chunk_count = chunk_locator_counts.get(loc, 0)
                if count != chunk_count:
                    if chunk_count == 0:
                        doc_report["fidelity_mismatches"].append({
                            "path": loc,
                            "reason": "missing_chunk_coverage"
                        })
                    else:
                        doc_report["fidelity_mismatches"].append({
                            "path": loc,
                            "reason": "duplicate_chunk_coverage"
                        })
                        
            for loc in chunk_locator_counts.keys():
                if loc not in parsed_locs_counts:
                    doc_report["fidelity_mismatches"].append({
                        "path": loc,
                        "reason": "missing_in_parsed"
                    })

            # 4. Strict Reverse Completeness on Raw Document bounds
            def is_valid_structural_skip(i):
                loc = raw_locators[i]
                t = block_map.get(loc, "").strip()
                if not t: return True
                t_upper = t.upper()
                
                # 1. Structural headings
                if re.match(r'^(CHƯƠNG|MỤC|PHẦN|TIỂU MỤC)\s+([IVXLCDM]+|\d+)(\.|:)?(\s|$)', t_upper): return True
                if t_upper == t: # Check if this uppercase line is part of a multi-line chapter title
                    for j in range(i - 1, -1, -1):
                        prev_t = block_map.get(raw_locators[j], "").strip()
                        if not prev_t: continue
                        prev_t_upper = prev_t.upper()
                        if re.match(r'^(CHƯƠNG|MỤC|PHẦN|TIỂU MỤC)\s+([IVXLCDM]+|\d+)(\.|:)?(\s|$)', prev_t_upper): return True
                        if prev_t_upper != prev_t: break # hit normal text
                
                # 2. Page numbers and PDF metadata
                if re.match(r'^Trang\s+\d+$', t_upper): return True
                if re.match(r'^CÔNG BÁO\s+/', t_upper): return True
                
                # 3. Exact document titles / headers
                if t_upper in ["CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM"]: return True
                if "ĐỘC LẬP" in t_upper and "TỰ DO" in t_upper and len(t_upper) < 50: return True
                
                allowed_exact = {
                    "QUỐC HỘI",
                    "CHỦ TỊCH QUỐC HỘI",
                    "LUẬT",
                    "BỘ LUẬT",
                }
                if t_upper in allowed_exact: return True
                
                # 4. Specific preamble/signatures/tails
                if re.match(r'^(LUẬT\s+|BỘ\s+LUẬT\s+)?SỐ:\s*\d+/\d+/QH\d+', t_upper): return True
                if re.match(r'^CĂN CỨ HIẾN PHÁP', t_upper): return True
                if "BỔ SUNG MỘT SỐ ĐIỀU THEO NGHỊ QUYẾT SỐ 203/2025/QH15" in t_upper: return True
                if re.match(r'^QUỐC HỘI BAN HÀNH', t_upper): return True
                if re.match(r'^HÀ NỘI, NGÀY \d+ THÁNG \d+ NĂM \d+$', t_upper): return True
                if re.match(r'^CỦA QUỐC HỘI KHÓA', t_upper): return True
                if re.match(r'^NGUYỄN SINH HÙNG', t_upper): return True
                if re.match(r'^NGUYỄN PHÚ TRỌNG', t_upper): return True

                if batch_num >= 3:
                    # 5. Digital signatures (usually at the very top of PDF or very end of DOCX files)
                    is_digital_signature = re.match(r'^(KÝ BỞI|NGƯỜI KÝ|EMAIL|CƠ QUAN|THỜI GIAN KÝ)\s*:', t_upper)
                    if is_digital_signature and len(t) < 100:
                        # Strictly constrain by position: first 30 or last 30 blocks
                        if i < 30 or i > len(raw_locators) - 30:
                            return True
                    
                    # 6. Combined headers & letterhead tables
                    # These only occur at the top of the document (first 30 blocks)
                    if i < 30:
                        if re.search(r'QUỐC HỘI\s+CỘNG H[OÒ]A XÃ HỘI CHỦ NGHĨA VIỆT NAM', t_upper): return True
                        if "QUỐC HỘI" in t_upper and "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in t_upper and "ĐỘC LẬP" in t_upper: return True
                    
                    # 7. Specific law titles / fragments in Batch 3 and 4
                    batch3_titles = {
                        "SỬA ĐỔI, BỔ SUNG MỘT SỐ ĐIỀU CỦA LUẬT BẢO HIỂM Y TẾ",
                        "SỐ 25/2008/QH12.",
                        "BẢO HIỂM XÃ HỘI",
                        "CƯ TRÚ",
                        "CÔNG NGHIỆP CÔNG NGHỆ SỐ",
                        "NHÀ GIÁO",
                        "LUẬT NHÀ GIÁO",
                        "LUẬT NHÀ BÁO",
                        "LUẬT VIỆC LÀM",
                        "THANH TRA",
                        "PHÍ VÀ LỆ PHÍ",
                        "AN TOÀN, VỆ SINH LAO ĐỘNG"
                    }
                    if t_upper in batch3_titles and i < 30: return True
                    
                    # 8. Promulgation commands (Lệnh công bố)
                    # These commands also appear only at the beginning of the file (first 50 blocks)
                    if i < 50:
                        if t_upper in {"LỆNH", "VỀ VIỆC CÔNG BỐ LUẬT", "NAY CÔNG BỐ:", "CHỦ TỊCH", "NƯỚC CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "LƯƠNG CƯỜNG", "VIỆT NAM;"}: return True
                        if re.match(r'^CHỦ TỊCH NƯỚC\s+CỘNG HÒA', t_upper): return True
                        if re.match(r'^SỐ:\s*\d+/\d+/L-CTN', t_upper): return True
                        if re.match(r'^CĂN CỨ ĐIỀU \d+ VÀ ĐIỀU \d+ CỦA HIẾN PHÁP', t_upper): return True
                        if re.match(r'^CĂN CỨ ĐIỀU \d+ CỦA LUẬT BAN HÀNH', t_upper): return True
                        if re.match(r'^ĐÃ ĐƯỢC QUỐC HỘI NƯỚC', t_upper): return True
                        if re.match(r'^THỨ \d+ THÔNG QUA NGÀY', t_upper): return True
                        if "LUẬT SỐ: 84/2015/QH13 | CỘNG HÒA" in t_upper: return True
                
                return False

            chunk_all_locators = set()
            for c in doc_chunks:
                if c.get("content_kind") == "normative":
                    for ref in c.get("source_refs", []):
                        if ref.get("locator"):
                            chunk_all_locators.add(ref.get("locator"))

            for i in range(len(raw_locators)):
                loc = raw_locators[i]
                if loc not in parsed_locs_counts and loc not in chunk_all_locators:
                    if not is_valid_structural_skip(i):
                        print(f"MISSING: {loc} -> {block_map.get(loc, '')[:200].encode('ascii', 'replace').decode('ascii')}")
                        doc_report["fidelity_mismatches"].append({
                            "path": loc,
                            "reason": "missing_in_parsed"
                        })
        else:
            doc_report["fidelity_mismatches"].append({
                "path": raw_path_str,
                "reason": "missing_raw_source"
            })
            
        # Post-fidelity checks
        for art in articles:
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
                    
        if doc_report["fidelity_mismatches"] or doc_report["duplicate_structural_paths"]:
            doc_report["status"] = "mismatched"
                
        report["documents"].append(doc_report)
        
    if any(d.get("status") == "mismatched" for d in report["documents"]):
        report["status"] = "FAIL"
        
    (fidelity_dir / batch_name).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
