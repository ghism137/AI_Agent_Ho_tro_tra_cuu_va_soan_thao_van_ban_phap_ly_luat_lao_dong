import re

def process_file():
    with open("reports/phase1-closeout/repair-2026-09-23/fidelity/build_p1r05_fidelity.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    start_idx = content.find('        # Unified fidelity check for DOCX and PDF')
    end_idx = content.find('        for idx, art in enumerate(articles):', start_idx)
    
    replacement = """        # Unified fidelity check for DOCX and PDF using chunks.jsonl
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
        elif raw_path_str.endswith(".pdf"):
            import pymupdf
            from backend.ingestion.pdf_text_extractor import extract_pdf_text
            pdf_path = ROOT / raw_path_str
            doc_len = len(pymupdf.open(pdf_path))
            raw_blocks = extract_pdf_text(pdf_path, first_page=1, last_page=doc_len)
            
        if raw_blocks:
            block_map = {}
            for b in raw_blocks:
                if b['kind'] == 'paragraph':
                    block_map[b['locator']] = unicodedata.normalize('NFC', b['text'].strip())
                elif b['kind'] == 'table':
                    for row_idx, r in enumerate(b.get('rows', [])):
                        text = ' | '.join(r)
                        loc = f"{b['locator']}/row:{row_idx+1}"
                        block_map[loc] = unicodedata.normalize('NFC', text.strip())

            # 1. Forward Completeness (Parsed <-> Raw)
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
                        txt_clean = re.sub(r'\\s+', '', txt).lower()
                        blk_clean = re.sub(r'\\s+', '', block_map[loc]).lower()
                        if txt_clean != blk_clean:
                            doc_report["fidelity_mismatches"].append({
                                "path": loc,
                                "reason": "content_mismatch"
                            })

            # 2. Reverse Completeness & Provenance via chunks.jsonl
            doc_chunks = chunks_by_doc.get(doc_id, [])
            if doc_chunks:
                from collections import Counter
                chunk_locator_counts = Counter()
                
                for c in doc_chunks:
                    # Validate chunk content matches raw text exactly (Provenance)
                    chunk_text = unicodedata.normalize('NFC', c.get("content", "").strip())
                    refs = c.get("source_refs", [])
                    raw_text_parts = []
                    
                    for ref in refs:
                        loc = ref.get("locator")
                        src = ref.get("source_id")
                        
                        if src != raw_source_id:
                            doc_report["fidelity_mismatches"].append({
                                "path": loc or "unknown",
                                "reason": "missing_provenance_to_raw"
                            })
                            
                        if loc:
                            if c.get("content_kind") == "normative":
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
                        # Chunk content might join with newline or space
                        raw_combined_clean = re.sub(r'\\s+', '', "".join(raw_text_parts)).lower()
                        chunk_clean = re.sub(r'\\s+', '', chunk_text).lower()
                        if chunk_clean != raw_combined_clean:
                            doc_report["fidelity_mismatches"].append({
                                "path": c.get("locator", "chunk"),
                                "reason": "chunk_content_mismatch"
                            })
                            
                # Verify that every parsed segment locator is covered EXACTLY once by normative chunks
                parsed_locs = {seg.get("locator") for art in articles for seg in art.get("content_segments", []) if seg.get("locator")}
                
                for loc in parsed_locs:
                    count = chunk_locator_counts.get(loc, 0)
                    if count == 0:
                        doc_report["fidelity_mismatches"].append({
                            "path": loc,
                            "reason": "missing_chunk_coverage"
                        })
                    elif count > 1:
                        doc_report["fidelity_mismatches"].append({
                            "path": loc,
                            "reason": "duplicate_chunk_coverage"
                        })
                        
                # Verify no extra locators in normative chunks that aren't in parsed (Reverse Completeness)
                for loc in chunk_locator_counts.keys():
                    if loc not in parsed_locs:
                        doc_report["fidelity_mismatches"].append({
                            "path": loc,
                            "reason": "missing_in_parsed"
                        })
        else:
            doc_report["fidelity_mismatches"].append({
                "path": raw_path_str,
                "reason": "missing_raw_source"
            })

"""
    new_content = content[:start_idx] + replacement + content[end_idx:]
    with open("reports/phase1-closeout/repair-2026-09-23/fidelity/build_p1r05_fidelity.py", "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    process_file()
