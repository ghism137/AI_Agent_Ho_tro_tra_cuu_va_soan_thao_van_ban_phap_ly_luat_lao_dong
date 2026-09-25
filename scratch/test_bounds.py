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
article_bounds = {}
current_art = None
start_idx = 0

for i, b in enumerate(blocks):
    if b['kind'] == 'paragraph':
        raw_locs.append(b['locator'])
        m = re.match(r'^Điều (\d+)[.\s]', b['text'], re.I)
        if m:
            art_num = m.group(1)
            if current_art:
                article_bounds[current_art]['end'] = i - 1
            current_art = art_num
            article_bounds[current_art] = {'start': i + 1}
    elif b['kind'] == 'table':
        for r_idx, _ in enumerate(b.get('rows', [])):
            raw_locs.append(f"{b['locator']}/row:{r_idx+1}")
            
if current_art:
    article_bounds[current_art]['end'] = len(blocks) - 1

for art in doc['articles']:
    art_num = str(art['article_number'])
    if art_num not in article_bounds:
        print('Not found in raw:', art_num)
        continue
    bounds = article_bounds[art_num]
    expected_locs = []
    for i in range(bounds['start'], bounds['end'] + 1):
        b = blocks[i]
        if b['kind'] == 'paragraph':
            # Skip non-normative headers
            if re.match(r'^(CHƯƠNG|MỤC|PHẦN|Chương|Mục|Phần)\b', b['text']):
                continue
            # skip footers
            if b['text'].strip() in ["CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "Độc lập - Tự do - Hạnh phúc", "CHỦ TỊCH QUỐC HỘI"]:
                continue
            # skip date
            if re.match(r'^Hà Nội, ngày.*năm', b['text']):
                continue
            if b['text'].strip() == "Nguyễn Sinh Hùng":
                continue
            expected_locs.append(b['locator'])
        elif b['kind'] == 'table':
            for r_idx, _ in enumerate(b.get('rows', [])):
                expected_locs.append(f"{b['locator']}/row:{r_idx+1}")
                
    actual_locs = [seg['locator'] for seg in art['content_segments'] if seg.get('locator')]
    
    missing = [l for l in expected_locs if l not in actual_locs]
    if missing:
        print('Article', art_num, 'is missing locators:', missing)
