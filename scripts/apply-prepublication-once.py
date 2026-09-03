"""Apply the author's pre-publication wording without rewriting evidence records."""
from pathlib import Path
import json, re
R=Path.cwd()

def edit(path, pairs):
    p=R/path;s=p.read_text()
    for old,new in pairs:
        assert old in s, (path, old[:90])
        s=s.replace(old,new)
    p.write_text(s.rstrip()+'\n')

edit('src/editorial/ResourcePages.tsx',[
 ('import { EditorialRiftVisual, MechanismStrip }', 'import { MechanismStrip }'),
 ('import { AnimationFeature } from "./ProgrammePages";', 'import { AnimationFeature } from "./ProgrammePages";\nimport { PaperConceptFigure, PaperCitation } from "./PaperPresentation";'),
 ('Part IV · integrated findings and analysis · v1.5','Part IV · provisional findings and analysis'),
 ('Flagship working paper v1.5 · Web overview','Working paper · Draft overview'),
 ('<a className="v2-button v2-button--dark" href={route("research/harmful-manipulation-election-security-v1.5-20260901.pdf")}>Read the full working paper · PDF</a>','<span className="paper-coming-soon">Full working paper — coming soon</span>'),
 ('<a href={route("research/harmful-manipulation-election-security-v1.3-20260901.pdf")}>Earlier snapshot · v1.3</a>',''),
 ('<div className="v2-wide-figure"><EditorialRiftVisual /><p className="v2-figure-caption">The three large stages are an organising frame, not a universal linear ladder. Every transition requires new evidence.</p></div>','<PaperConceptFigure />'),
 ('In this working version','Inside the working draft'),
 ('The full 33-page PDF includes the appendices and complete references; this page is a web overview, not the full manuscript.','The full manuscript is being prepared for publication. This page is a provisional overview; the source-linked bibliography is available now.'),
 ('Flagship v1.5 · overview, full PDF and earlier edition','Draft overview · full working paper coming soon'),
 ('Part IV · published beta.3 dataset; original evidence grades','Part IV · source-linked dataset; original evidence grades'),
 ('The production Atlas remains beta.3:', 'The source Atlas remains unchanged:'),
 ('The complete manuscript adds 21 external references and the separately identified project review, including version-specific preprints, adjacent-domain studies and the Community Notes correction.', 'The working manuscript draws on additional external sources and the separately identified project review, including preprints, adjacent-domain studies and the Community Notes correction.'),
 ('<section className="v2-citation"><p className="v2-eyebrow">Citation</p><p>Guerrero, Miguel. 2026. <em>Harmful Manipulation and Election Security: The Capability–Deployment–Effect Gap.</em> ERA:AI Summer Research Fellowship, Cambridge. Flagship working paper, v1.5, 1 September 2026.</p></section>','<PaperCitation />'),
 ('Published the v1.5 working paper, preserved earlier snapshots and labelled unpublished artifacts.', 'Shared an early manuscript snapshot for review and labelled unfinished artifacts. That snapshot was not a formal paper release.'),
 ('without upgrading empirical grades or the v1.3 PDF.', 'without upgrading empirical grades or treating the working manuscript as a formal release.'),
 ('Source-linked policy review and full manuscript published','Source-linked policy review and draft manuscript'),
 ('original review workbook and full v1.3 working-paper PDF. Historical Atlas beta.3 flags remain unchanged.', 'original review workbook and an early manuscript snapshot for review. The Atlas evidence flags remain unchanged.'),
 ('Paper v1.3 · what works, and for whom?','Working paper · policy evidence and its limits'),
 ('Canonical synchronization · Atlas beta.3 and paper v1.2','Policy Atlas and working-paper alignment'),
 ('Flagship working paper v1.0','Initial working-paper synthesis'),
])
p=R/'src/editorial/ResourcePages.tsx';s=p.read_text();s=s.replace('<blockquote className="v2-rule-quote">A safer agent is not necessarily a less powerful operator.</blockquote>', '<blockquote className="v2-rule-quote">A safer agent is not necessarily a less powerful operator.</blockquote>\n      <PaperCitation />')
s=s.replace('<section className="v2-update-list">', '<section className="v2-update-list"><article><time>3 Sep 2026</time><div><h2>Publication status clarified</h2><p>The full working paper is forthcoming. Earlier numbering identified working copies, not formal public releases. The website now uses unnumbered draft labels, a short citation and the existing artistic CDE illustration in place of the paper overview’s SVG. Research records and source references are unchanged.</p></div></article>',1)
p.write_text(s)
edit('src/editorial/ProgrammePages.tsx',[
 ('Read the working paper</a>','Read the draft overview</a>'),
 ('v1.5 working draft · full PDF','Draft overview · full paper coming soon'),
])
edit('src/editorial/EditorialShell.tsx',[
 ('Web overview and full v1.5 working paper: The Capability–Deployment–Effect Gap, with the 1 September policy review.', 'A draft overview of The Capability–Deployment–Effect Gap. The full working paper is forthcoming; no formal paper release has taken place.'),
])
edit('src/components/ResearchStatus.tsx',[
 ('<p><strong>Current working version: v1.5, 1 September 2026.</strong> This page is an overview; the complete manuscript and bibliography are linked below. Earlier PDF snapshots remain available. This publication update does not add experiments or change dataset grades.</p>', '<p><strong>Unpublished working draft.</strong> This page presents the argument in progress, not a formally released paper. The full manuscript is forthcoming; the bibliography and research records are available for inspection.</p>'),
])
edit('src/editorial/PolicyPage.tsx',[
 ('The current v1.5 manuscript retains this review and adds narrative and source qualifications.', 'The working manuscript incorporates this review and its source qualifications.'),
 ('The published Atlas beta.3 and its empirical claim-check flags remain unchanged;', 'The Atlas and its empirical claim-check flags remain unchanged;'),
])
edit('src/editorial/ReferencesPage.tsx',[
 ('version: string; manuscriptVersion: string;', 'status: string; manuscriptStatus: string;'),
 ('Manuscript v{library?.manuscriptVersion ?? "1.5"} · Source snapshot: 1 September 2026.', 'Working-draft bibliography · source snapshot: 1 September 2026.'),
])
edit('scripts/build-reference-page.py', [('Cited in the flagship working paper v1.5','Cited in the working draft')])
edit('paper/index.html',[('Working paper v1.5','Working paper')])
edit('README.md',[
 ('The [current working paper](https://miguelguerrero.eu/agencytransfer/paper/) is v1.5 (1 September 2026); previous snapshots are retained.', 'The [working-paper overview](https://miguelguerrero.eu/agencytransfer/paper/) is an unpublished draft. The full paper is coming soon; no formal paper release has taken place. Historical working-copy filenames are retained for provenance, not presented as public release numbers.'),
])
p=R/'CITATION.cff';s=p.read_text();s=re.sub(r'^  (?:version|date-released):.*\n','',s,flags=re.M);s=s.replace('notes: "Working paper; not peer reviewed. Earlier snapshots remain available."','notes: "Unpublished working draft; full manuscript forthcoming. No formal public paper release."');p.write_text(s)
p=R/'public/research/references.json';d=json.loads(p.read_text());d.pop('manuscriptVersion',None);d['manuscriptStatus']='unpublished_working_draft'
for c in d['collections']:
 if c['id']=='flagship':c['label']='Flagship working draft'
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
p=R/'programme/project-manifest.json';d=json.loads(p.read_text());a=next(x for x in d['artifacts'] if x['id']=='flagship-paper');a.update(status='unpublished_working_draft',source_url=None,source_version=None,public_release_version=None,publication_note='Public draft overview only. Full working paper coming soon. Historical manuscript filenames identify working copies, not formal public releases.');d['programme']['last_updated']='2026-09-03'
for k,v in d.items():
 if isinstance(v,list) and v and isinstance(v[0],str): d[k]=[t.replace('manuscript v1.3','working manuscript') for t in v]
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
old=json.loads(__import__('subprocess').check_output(['git','show','HEAD:public/research/references.json'],text=True));new=json.loads((R/'public/research/references.json').read_text());assert new['records']==old['records'] and new['counts']==old['counts']
edit('scripts/review-publication.py',[
 ("assert page.locator('a[href$=\"v1.5-20260901.pdf\"]').count()==1", "assert page.locator('.paper-coming-soon').inner_text() == 'Full working paper — coming soon'\n     assert page.locator('a[href$=\"v1.5-20260901.pdf\"]').count()==0"),
 ("assert page.locator('a[href$=\"v1.3-20260901.pdf\"]').count()==1", "assert page.locator('a[href$=\"v1.3-20260901.pdf\"]').count()==0"),
])
print('Pre-publication wording applied. Source records and historical manuscript bytes preserved.')
