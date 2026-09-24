import json

parsed = json.load(open('data/staging/phase1-candidate/parsed.json', encoding='utf-8'))
doc = parsed['doc:10/2012/QH13']
schema = {
    'keys': list(doc.keys()),
    'first_article': doc['articles'][0] if 'articles' in doc else {}
}
with open('temp_schema.json', 'w', encoding='utf-8') as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)
