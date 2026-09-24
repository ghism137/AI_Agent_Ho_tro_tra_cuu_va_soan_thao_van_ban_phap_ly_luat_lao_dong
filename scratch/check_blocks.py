from backend.ingestion.docx_extractor import extract_docx
from pathlib import Path
import json

p = json.load(open('data/staging/phase1-candidate/parsed.json', encoding='utf-8'))
d = p['doc:10/2012/QH13']

blocks = extract_docx(Path('data/raw/official/Bộ-luật-10-2012-QH13.docx'))
block_map = {}
for b in blocks:
    if b['kind'] == 'paragraph':
        block_map[b['locator']] = b['text']
    elif b['kind'] == 'table':
        for row_idx, r in enumerate(b.get('rows', [])):
            block_map[f"{b['locator']}/row:{row_idx+1}"] = ' | '.join(r)
            
mismatches = []
for a in d['articles']:
    for seg in a.get('content_segments', []):
        loc = seg['locator']
        txt = seg['text']
        if loc not in block_map:
            mismatches.append((loc, 'Not in blocks', txt))
        elif block_map[loc] != txt:
            mismatches.append((loc, 'Text mismatch', txt, block_map[loc]))
print(f'Mismatches: {len(mismatches)}')
if mismatches:
    print(mismatches[:3])
