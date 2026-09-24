import json
import unicodedata
from pathlib import Path
import sys

ROOT = Path('C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động')
sys.path.insert(0, str(ROOT))
from backend.ingestion.docx_extractor import extract_docx

parsed = json.load(open('data/staging/phase1-candidate/parsed.json', encoding='utf-8'))
doc = parsed['doc:10/2012/QH13']
blocks = extract_docx(ROOT / 'data/raw/word/Bộ-luật-10-2012-QH13.docx')

block_map = {}
for b in blocks:
    if b['kind'] == 'paragraph':
        block_map[b['locator']] = unicodedata.normalize('NFC', b['text'].strip())
    elif b['kind'] == 'table':
        for row_idx, r in enumerate(b.get('rows', [])):
            text = ' | '.join(r)
            block_map[f"{b['locator']}/row:{row_idx+1}"] = unicodedata.normalize('NFC', text.strip())

for a in doc['articles']:
    for seg in a.get('content_segments', []):
        if seg.get('locator') == 'body/p:947':
            txt = unicodedata.normalize('NFC', seg.get('text', '').strip())
            b_txt = block_map['body/p:947']
            print('TXT:', repr(txt))
            print('BLK:', repr(b_txt))
