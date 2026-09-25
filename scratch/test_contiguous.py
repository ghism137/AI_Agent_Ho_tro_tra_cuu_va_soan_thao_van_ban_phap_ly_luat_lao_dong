import json
import sys
sys.path.insert(0, '.')
from backend.ingestion.docx_extractor import extract_docx
from pathlib import Path

parsed = json.load(open('data/staging/phase1-candidate/parsed.json', encoding='utf-8'))
doc = parsed['doc:10/2012/QH13']
blocks = extract_docx(Path('data/raw/official/Bộ-luật-10-2012-QH13.docx'))

raw_locs = []
for b in blocks:
    if b['kind'] == 'paragraph':
        raw_locs.append(b['locator'])
    elif b['kind'] == 'table':
        for i, _ in enumerate(b.get('rows', [])):
            raw_locs.append(f"{b['locator']}/row:{i+1}")

for art in doc['articles']:
    locs = [seg['locator'] for seg in art['content_segments'] if seg.get('locator')]
    indices = [raw_locs.index(l) for l in locs if l in raw_locs]
    if not indices: continue
    
    # Check if indices are exactly contiguous
    is_contiguous = (max(indices) - min(indices) + 1 == len(indices))
    if not is_contiguous:
        missing = [raw_locs[i] for i in range(min(indices), max(indices) + 1) if i not in indices]
        print('Article', art['article_number'], 'is not contiguous! Gap missing locators:', missing)
