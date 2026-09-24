import json
import os

parsed_file = 'data/staging/phase1-candidate/parsed.json'
parsed = json.load(open(parsed_file, encoding='utf-8'))

doc_map = {
    '10/2012/QH13': 'data/cleaned/Bộ-luật-10-2012-QH13.json',
    '12/2012/QH13': 'data/cleaned/Luật-12-2012-QH13.json'
}

for doc_num, path in doc_map.items():
    doc_id = f"doc:{doc_num}"
    if doc_id not in parsed:
        continue
    p_articles = parsed[doc_id]['articles']
    
    # group parsed content by article_number
    grouped = {}
    for a in p_articles:
        anum = a.get('article_number')
        if not anum:
            continue
        if anum not in grouped:
            grouped[anum] = []
        grouped[anum].append(a.get('content', ''))
        
    c = json.load(open(path, encoding='utf-8'))
    for a in c['articles']:
        anum = a.get('article_number')
        if anum in grouped:
            full_text = "\n".join(grouped[anum])
            if a.get('content') != full_text:
                print(f"Fixing {doc_num} article {anum}")
                a['content'] = full_text
                
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(c, f, ensure_ascii=False, indent=2)

print("Done")
