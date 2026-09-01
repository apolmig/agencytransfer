#!/usr/bin/env python3
"""Render an accessible static bibliography from the editable public source index."""
from pathlib import Path
import json, html
ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'public/research/references.json'
data = json.loads(source.read_text())
e = html.escape
parts = ['''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Full bibliography · Agency Transfer · Working draft</title><style>body{max-width:850px;margin:40px auto;padding:0 24px;background:#f8f7f4;color:#242424;font:17px/1.65 Georgia,serif}h1{font-size:34px;font-weight:400;line-height:1.2}h2{font-size:22px;font-weight:400}h3{font-size:19px;font-weight:400;line-height:1.3}a{color:inherit;text-underline-offset:3px}li{border-top:1px solid #d7d3cb;padding:18px 0;overflow-wrap:anywhere;scroll-margin-top:20px}ol{padding-left:24px}small{color:#5d5b57;font:12px/1.5 Arial,sans-serif}p{margin:8px 0}nav{display:flex;gap:22px;flex-wrap:wrap}details{font-size:14px;margin-top:12px}summary{cursor:pointer;min-height:35px}:focus-visible{outline:2px solid #285e60;outline-offset:4px}@media print{body{max-width:none;margin:0}li{break-inside:avoid}}</style></head><body><header><small>WORKING DRAFT · 1 SEPTEMBER 2026</small><h1>References and source library</h1><p>The flagship bibliography and wider recorded reading. Inclusion is not endorsement, independent verification or a statement that every source received full-text review.</p><nav><a href="../references/">Search and filter</a><a href="#flagship">Flagship citations</a><a href="#wider">Wider source record</a><a href="../paper/">Working paper</a></nav></header>''']
labels={c['id']:c['label'] for c in data['collections']}
for scope, heading in [('flagship','Cited in the flagship working paper v1.5'),('wider','Wider reading and source records')]:
 records=[r for r in data['records'] if (r['scope']=='flagship')==(scope=='flagship')]
 parts.append(f'<section id="{scope}"><h2>{heading}</h2><p>{len(records)} source records.</p><ol>')
 for r in records:
  title=f'<a href="{e(r["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{e(r["title"])}</a>' if r['url'].startswith(('http://','https://')) else e(r['title'])
  parts.append(f'<li id="{r["id"]}"><small>{e(r["category"])} · {e(r["recordedStatus"])}</small><h3>{title}</h3><p>{e(r["authors"] or "Author not specified in source record")} · {e(r["year"] or "Date not recorded")}</p>')
  for c in r['citations']:parts.append(f'<p>{e(c)}</p>')
  if r.get('metadataNote'):parts.append(f'<p><small>{e(r["metadataNote"])}</small></p>')
  state=r['linkCheck']['status'].replace('_',' ')
  parts.append(f'<small>Link: {e(state)}. A link check is not an evidence review.</small><details><summary>Source context and provenance</summary>')
  if r['boundary']:parts.append(f'<p>Recorded limit: {e(r["boundary"])}</p>')
  for p in r['provenance']:parts.append(f'<p><strong>{e(labels[p["collection"]])}</strong> · {e(p["locator"])}<br>{e(p["title"])}</p>')
  parts.append('</details></li>')
 parts.append('</ol></section>')
parts.append('<footer><p>Exact identifiers and matching titles consolidate repeat records. Original locators and recorded variants are retained in the <a href="references.json">JSON index</a>. Private documents and raw operational material are not linked.</p></footer></body></html>')
(ROOT/'public/research/references.html').write_text('\n'.join(parts)+'\n')
print(f'Rendered {len(data["records"])} references; {data["counts"]["flagshipCitations"]} flagship citations.')
