import json
import sys
import re
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
    if not locs: continue
    first_loc = locs[0]
    idx = raw_locs.index(first_loc)
    prev_idx = idx - 1
    if prev_idx >= 0:
        prev_loc = raw_locs[prev_idx]
        prev_block_txt = [b['text'] for b in blocks if b.get('locator') == prev_loc.split('/row')[0]]
        if prev_block_txt:
            print('Art', art['article_number'], 'prev text:', repr(prev_block_txt[0][:50]))
    if art['article_number'] == '10': break
