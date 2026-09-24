import json
import unicodedata

d = json.load(open('data/staging/phase1-candidate/parsed.json', encoding='utf-8'))
doc = d.get('doc:10/2012/QH13')
ext = json.load(open('data/cleaned/Bộ-luật-10-2012-QH13.json', encoding='utf-8'))

ext_arts = {str(a.get('article_number')): unicodedata.normalize('NFC', a.get('content', '')) for a in ext['articles']}

mismatches = 0
for art in doc['articles']:
    art_num = str(art.get('article_number'))
    content = unicodedata.normalize('NFC', art.get('content', ''))
    
    if art_num not in ext_arts:
        print("Missing in extracted:", art_num)
        mismatches += 1
        continue
        
    ext_content = ext_arts[art_num]
    # Check if content is a substring
    if content.strip() not in ext_content:
        mismatches += 1
        if mismatches <= 3:
            print("MISMATCH ON", art_num)
            print("CHUNK:", repr(content.strip()))
            print("EXTRACTED:", repr(ext_content))

print("Total mismatches:", mismatches)
