import re

def process_file():
    with open("reports/phase1-closeout/repair-2026-09-23/fidelity/build_p1r05_fidelity.py", "r", encoding="utf-8") as f:
        content = f.read()

    start_idx = content.find('        if raw_path_str.endswith(".docx"):')
    end_idx = content.find('        for idx, art in enumerate(articles):')
    
    replacement = """        # Unified fidelity check for DOCX and PDF
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
            
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
            # Flatten blocks for map and list
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
                        
            # 1. Check Forward Completeness & Internal Reverse Completeness (Parsed <-> Raw)
            for art in articles:
                locs = [seg.get("locator") for seg in art.get("content_segments", []) if seg.get("locator")]
                
                # Check forward: every segment in parsed must exist in raw with matching text
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
                            
                # Check internal reverse completeness: no raw block in the article's range can be missing from parsed
                indices = [raw_locators.index(l) for l in locs if l in raw_locators]
                if indices:
                    min_idx, max_idx = min(indices), max(indices)
                    for i in range(min_idx, max_idx + 1):
                        if raw_locators[i] not in locs:
                            doc_report["fidelity_mismatches"].append({
                                "path": raw_locators[i],
                                "reason": "missing_in_parsed"
                            })

            # 2. Check chunks.jsonl against parsed.json (PDF chunks)
            doc_chunks = chunks_by_doc.get(doc_id, [])
            if doc_chunks:
                # Count locators in chunks to prevent duplicate masking
                from collections import Counter
                chunk_locator_counts = Counter()
                for c in doc_chunks:
                    refs = c.get("source_refs", [])
                    for ref in refs:
                        loc = ref.get("locator")
                        src = ref.get("source_id")
                        if loc:
                            chunk_locator_counts[loc] += 1
                            if loc not in raw_locators:
                                doc_report["fidelity_mismatches"].append({
                                    "path": loc,
                                    "reason": "invalid_chunk_locator"
                                })
                        if src != raw_source_id:
                            doc_report["fidelity_mismatches"].append({
                                "path": loc or "unknown",
                                "reason": "missing_provenance_to_raw"
                            })
                            
                # Verify that every parsed segment locator is covered EXACTLY once by chunks
                for art in articles:
                    for seg in art.get("content_segments", []):
                        loc = seg.get("locator")
                        if loc:
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
                                
                # Verify no extra locators in chunks that aren't in parsed
                parsed_locs = {seg.get("locator") for art in articles for seg in art.get("content_segments", []) if seg.get("locator")}
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
