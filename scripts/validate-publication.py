"""Check references and immutable public artifacts without network access."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'public/research/references.json').read_text())
assert len(data['records'])==data['counts']['records'] and len(data['records'])>0
assert len({r['id'] for r in data['records']})==len(data['records'])
assert sum(len(r['citations']) for r in data['records'])==data['counts']['flagshipCitations']
assert sum(len(r['provenance']) for r in data['records'])==data['counts']['sourceEntries']
collections={c['id'] for c in data['collections']}
for r in data['records']:
 assert r['title'] and r['provenance']
 assert r['scope'] in ('flagship','review','considered')
 assert not r['url'] or r['url'].startswith(('http://','https://'))
 assert all(p['collection'] in collections for p in r['provenance'])
 assert all('drive.google.com' not in u and 'agencytransfer-controlled' not in u for u in [r['url'],*r['alternateUrls']])
 if r['scope']=='flagship':assert r['citations']
html=(ROOT/'public/research/references.html').read_text()
assert all(f'id="{r["id"]}"' in html for r in data['records'])
meta=json.loads((ROOT/'public/research/flagship-v1.5-metadata.json').read_text())
pdf=ROOT/'public'/meta['publicPath']
assert hashlib.sha256(pdf.read_bytes()).hexdigest()==meta['sha256'] and meta['pages']==33
assert (ROOT/'references/index.html').exists()
print(f"Publication record validated: {data['counts']['records']} references, {data['counts']['flagshipCitations']} flagship citations, {data['counts']['sourceEntries']} original entries; exact v1.5 PDF.")
