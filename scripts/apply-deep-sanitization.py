#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")


def replace(path: str, old: str, new: str, count: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"{path}: expected {count} occurrence(s), found {actual}: {old[:100]!r}")
    write(path, text.replace(old, new, count))


def regex_replace(path: str, pattern: str, replacement: str, count: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    updated, actual = re.subn(pattern, replacement, text, count=count, flags=re.S)
    if actual != count:
        raise SystemExit(f"{path}: expected {count} regex match(es), found {actual}: {pattern[:100]!r}")
    write(path, updated)


# Persistent status and metadata: one concise notice rather than repeated apologies.
shell = ROOT / "src/editorial/EditorialShell.tsx"
text = shell.read_text(encoding="utf-8")
text = re.sub(
    r'<time dateTime="2026-09-0[12]">Updated: [12] September 2026</time>',
    '<time dateTime="2026-09-03">Updated: 3 September 2026</time>',
    text,
)
text, n = re.subn(
    r'<div><span aria-hidden="true" /><strong>[^<]*</strong><p>.*?</p></div>',
    '<div><span aria-hidden="true" /><strong>Working draft</strong><p>Research in progress · not peer reviewed · findings and recommendations may change.</p></div>',
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("EditorialShell: draft bar not found")
text = text.replace(
    "Draft research by Miguel Guerrero · ERA:AI Summer Research Fellowship, Cambridge · 2026. Programme results, interpretations and recommendations remain provisional; no independent replication.",
    "Miguel Guerrero · ERA:AI Summer Research Fellowship, Cambridge · 2026. Working draft; findings and recommendations remain provisional.",
)
all_other_tsx = "\n".join(
    path.read_text(encoding="utf-8", errors="ignore")
    for path in ROOT.glob("src/**/*.tsx")
    if path != shell
)
if "RIFT_IMAGE" not in all_other_tsx:
    text = re.sub(r'\nexport const RIFT_IMAGE = asset\("[^"]+"\);', "", text)
write("src/editorial/EditorialShell.tsx", text)


# Homepage and Part I: preserve the hook, reduce the visible argument.
path = ROOT / "src/editorial/ProgrammePages.tsx"
text = path.read_text(encoding="utf-8")
text = text.replace("Four audits of one influence system", "Four workstreams, one research question")
text = text.replace(
    "The programme keeps technical traces, model evaluations, election records, and policy evidence separate. Each part observes a different node and stops at its own claim boundary.",
    "The programme follows one problem across four evidence layers: capability and operations, evaluation, field evidence, and policy. Each layer has its own claim boundary.",
)
text = text.replace("What works—and for whom?", "What appears useful—and for whom?", 1)
text = text.replace(
    "Concrete controls, evidence and limits. Adoption is not the same as effectiveness.",
    "Concrete controls, observed effects and open questions. Adoption is not the same as effectiveness.",
)
text = text.replace("Featured draft artifact", "Featured research artifact")
text = re.sub(
    r'\n\s*<p className="publication-pending">Poster and standalone white paper: not yet published\.[^<]*</p>',
    "",
    text,
)
text, n = re.subn(
    r'<div className="v2-actions">\s*<a className="v2-button v2-button--dark" href=\{route\("[^"]*"\)\}>[^<]+</a>\s*<a className="v2-button" href=\{route\("[^"]*"\)\}>[^<]+</a>\s*</div>',
    '<div className="v2-actions"><a className="v2-button v2-button--dark" href={route("paper/")}>Read the working paper</a><a className="v2-button" href={route("explainers/")}>See the CDE Gap</a></div>',
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("ProgrammePages: hero actions not found")
part_i_pattern = r'<section className="v2-three-column">\s*<article><p className="v2-eyebrow">Provisional programme record</p>.*?</section>'
part_i_replacement = '''<section className="v2-evidence-pair v2-evidence-pair--sanitized">
        <article><p className="v2-eyebrow">What the pilot suggests</p><h2>Low-cost systems can assist planning and prototyping</h2><p>The author-reported pilot produced multi-step, multimodal prototypes. A closer-inspected subset shows campaign-planning assistance after some tactical refusals. This supports a bounded capability claim, not a reliable success rate or a live operation.</p></article>
        <article><p className="v2-eyebrow">What it does not show</p><h2>No deployment, audience contact, persuasion or electoral effect</h2><p>The work did not research voters, contact real people, distribute content, run a feedback loop, or estimate behaviour. A separate intervention study also failed to produce an independently reloadable model package.</p></article>
      </section>
      <p className="v2-next-step"><strong>Next study:</strong> reconcile the full budget, freeze exact system versions, compare with a human-only baseline, and use blinded review in a closed synthetic environment.</p>'''
text, n = re.subn(part_i_pattern, part_i_replacement, text, count=1, flags=re.S)
if n != 1:
    raise SystemExit("ProgrammePages: Part I three-column block not found")
text = text.replace("Part I · Capability and operations · Draft / work in progress", "Part I · Capability and operations")
write("src/editorial/ProgrammePages.tsx", text)


# Keep the $10 hook first; place the full boundary later and behind an explicit disclosure.
status_path = ROOT / "src/components/ResearchStatus.tsx"
text = status_path.read_text(encoding="utf-8")
match = re.search(
    r'export function BudgetBoundary\(\) \{\s*return \(\s*(<aside className="research-update budget-boundary".*?</aside>)\s*\);\s*\}',
    text,
    flags=re.S,
)
if not match:
    raise SystemExit("ResearchStatus: BudgetBoundary not found")
block = match.group(1)
inner = re.sub(r'^<aside className="research-update budget-boundary"[^>]*>', "", block)
inner = re.sub(r'</aside>$', "", inner)
new_block = '''<details className="research-update budget-boundary">
      <summary>What the $10 figure includes—and excludes</summary>
      <div className="budget-boundary__body">''' + inner + '''</div>
    </details>'''
text = text[: match.start(1)] + new_block + text[match.end(1) :]
text = text.replace(
    '<p><strong>Draft manuscript; evolving website.</strong> The PDF is the preserved v1.3 snapshot.',
    '<p><strong>Version note.</strong> The PDF is a preserved manuscript snapshot.',
)
write("src/components/ResearchStatus.tsx", text)


# Part III: the rift image already has one primary home and explainer role.
evidence_path = ROOT / "src/editorial/EvidencePages.tsx"
text = evidence_path.read_text(encoding="utf-8")
text = text.replace("Part III · Field evidence · Draft / work in progress", "Part III · Field evidence")
text, n = re.subn(
    r'\s*<div className="v2-wide-figure"><EditorialRiftVisual />.*?</div>\s*',
    "\n",
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("EvidencePages: duplicate CDE visual not found")
if "EditorialRiftVisual" not in text.replace('import { EditorialRiftVisual } from "./EditorialVisuals";', ""):
    text = text.replace('import { EditorialRiftVisual } from "./EditorialVisuals";\n', "")
write("src/editorial/EvidencePages.tsx", text)


# Part IV: do not headline a provisional review as settled effectiveness.
policy_path = ROOT / "src/editorial/PolicyPage.tsx"
text = policy_path.read_text(encoding="utf-8")
text = text.replace('title="What works—and for whom?"', 'title="What appears useful—and for whom?"')
text = text.replace("What works—and for whom?", "What appears useful—and for whom?")
text = text.replace(
    "The intervention portfolio is broad. The evidence is not. This review asks what each control changes, under which conditions, and whose agency it protects.",
    "The intervention portfolio is broad; evidence of effectiveness is uneven. This review separates what has been adopted, what has been measured, and what remains a proposal.",
)
write("src/editorial/PolicyPage.tsx", text)

examples_path = ROOT / "src/editorial/PolicyExamples.tsx"
text = examples_path.read_text(encoding="utf-8")
match = re.search(
    r'<div className="policy-example-grid">\s*\{examples\.map\(\(item\) => \(\s*<article className="policy-example".*?</article>\s*\)\)\}\s*</div>',
    text,
    flags=re.S,
)
if not match:
    raise SystemExit("PolicyExamples: current render block not found")
replacement = '''<div className="policy-example-list">
        {examples.map((item) => (
          <details className="policy-example" key={item.id} id={`example-${item.id}`}>
            <summary><span><small>{item.status}</small><strong>{item.title}</strong></span><i aria-hidden="true">+</i></summary>
            <div className="policy-example__body">
              <p>{item.example}</p>
              <p><strong>Evidence so far.</strong> {item.evidence}</p>
              <p><strong>Provisional recommendation.</strong> {item.recommendation}</p>
              <h4>What to measure and where the claim stops</h4><p>{item.measure}</p><p>{item.qualification}</p>
              <p className="research-update-sources">{item.sources.map(([label, href], i) => <span key={href}>{i ? " · " : ""}<a href={href} target="_blank" rel="noreferrer">{label}</a></span>)}</p>
            </div>
          </details>
        ))}
      </div>'''
text = text[: match.start()] + replacement + text[match.end() :]
text = text.replace("What to do now, what to test, and what not to claim", "Concrete examples: what to do, test and measure")
text = text.replace(
    "Legal duties and evidence of effectiveness answer different questions. The examples below distinguish an adopted obligation, a measured component effect and our provisional recommendation. None establishes end-to-end protection from harmful manipulation.",
    "Each example separates legal status, measured evidence, a provisional recommendation and the remaining uncertainty. None establishes end-to-end protection.",
)
write("src/editorial/PolicyExamples.tsx", text)


# Paper and artifacts: keep the overview short; the PDF is the full record.
resources_path = ROOT / "src/editorial/ResourcePages.tsx"
text = resources_path.read_text(encoding="utf-8")
match = re.search(r'(<section className="v2-paper-sections">.*?</section>)', text, flags=re.S)
if not match:
    raise SystemExit("ResourcePages: paper contents section not found")
if "paper-contents-disclosure" not in match.group(1):
    wrapped = '<details className="paper-contents-disclosure"><summary>What is in the working paper</summary>' + match.group(1) + "</details>"
    text = text[: match.start()] + wrapped + text[match.end() :]
text = text.replace("One programme, several forms", "Published research and supporting artifacts")
text = text.replace(
    "All programme outputs are drafts and work in progress, not peer-reviewed conclusions. The paper supplies the argument; datasets and tools supply inspectable, provisional records. External sources retain their own publication status.",
    "The working paper is the main synthesis. The Registry, evidence indexes, policy review, references and explainers document the underlying work. Unpublished outputs are labelled separately.",
)
text = text.replace("Explain the mechanism, not the spectacle", "The CDE Gap, explained")
text = text.replace(
    "These artifacts make the system legible. Synthetic scenarios are illustrations, not observations of real campaigns, authentic exposure, behaviour change, or electoral effect.",
    "A short, user-controlled explanation of the programme’s central distinction. Synthetic scenarios remain illustrations, not evidence of real campaigns or effects.",
)
write("src/editorial/ResourcePages.tsx", text)


# References: distinguish a source record from an independently reviewed evidence base.
references_path = ROOT / "src/editorial/ReferencesPage.tsx"
text = references_path.read_text(encoding="utf-8")
text = text.replace(
    "The flagship bibliography and the wider reading behind the programme. Search by author, title or subject. Review depth varies; inclusion is not endorsement.",
    "A searchable source record for the flagship paper and the wider programme. Inclusion records consideration or citation; it does not imply full-text review, endorsement or independent verification.",
)
write("src/editorial/ReferencesPage.tsx", text)


# Final editorial layer: smaller hierarchy, consistent line lengths and progressive disclosure.
write(
    "src/editorial/sanitization.css",
    r'''/* Deep sanitization pass · 3 September 2026.
   Editorial consistency only; no Registry or empirical-data changes. */
:root{--san-ink:#1f1f1d;--san-muted:#66635e;--san-rule:#d8d4cc;--san-paper:#fbfaf7;--san-accent:#7f1d2d}
html{scroll-behavior:smooth}body.editorial-v2-active{background:var(--san-paper);color:var(--san-ink);-webkit-font-smoothing:antialiased}
.v2-site .v2-main{width:min(1180px,calc(100% - 48px));margin-inline:auto}.v2-site .v2-header{width:min(1240px,calc(100% - 40px));min-height:68px;padding-block:12px;background:color-mix(in srgb,var(--san-paper) 94%,transparent);backdrop-filter:blur(12px)}
.v2-site .v2-header nav{scrollbar-width:none}.v2-site .v2-header nav::-webkit-scrollbar{display:none}.v2-site .v2-header a:focus-visible,.v2-site button:focus-visible,.v2-site summary:focus-visible,.v2-site input:focus-visible,.v2-site select:focus-visible{outline:2px solid var(--san-accent);outline-offset:3px}
.v2-site h1,.v2-site h2,.v2-site h3{text-wrap:balance}.v2-site p,.v2-site li,.v2-site dd{text-wrap:pretty}.v2-site .v2-hero{padding-block:clamp(44px,6vw,82px);gap:clamp(28px,5vw,70px)}
.v2-site .v2-hero h1{font-size:clamp(2.45rem,5.2vw,4.55rem);line-height:.98;letter-spacing:-.045em}.v2-site .v2-hero h2{font-size:clamp(1.25rem,2.2vw,1.9rem)}.v2-site .v2-deck{max-width:65ch;font-size:clamp(1rem,1.4vw,1.17rem);line-height:1.58}.v2-site .v2-plain-boundary{max-width:62ch}.v2-site .v2-actions{margin-top:26px}.v2-site .v2-button{min-height:44px;padding:11px 17px}
.v2-site .v2-parts--simple{padding-block:clamp(36px,5vw,66px)}.v2-site .v2-parts--simple .v2-part-card,.v2-site .v2-parts--simple .v2-part-card--featured{min-height:0;padding:clamp(20px,2.4vw,30px)}.v2-site .v2-part-card h2{font-size:clamp(1.35rem,2vw,1.8rem)}.v2-site .v2-part-card h3{font-size:.98rem;line-height:1.45;margin-top:18px}.v2-site .v2-part-card>p:not(:first-child){font-size:.91rem;line-height:1.55}
.v2-site .v2-page-lead{max-width:880px;padding-block:clamp(46px,7vw,86px) clamp(34px,5vw,58px)}.v2-site .v2-page-lead h1{max-width:16ch;font-size:clamp(2.15rem,4.8vw,4rem);line-height:1.03}.v2-site .v2-boundary{max-width:760px;padding:16px 18px}.v2-site .v2-evidence-pair--sanitized{margin-block:42px}.v2-site .v2-evidence-pair--sanitized article{padding-top:18px}.v2-site .v2-next-step{max-width:72ch;margin:-12px 0 42px;color:var(--san-muted)}
.v2-site .budget-boundary{max-width:860px;margin-block:40px;padding:0;background:transparent;border:0}.v2-site .budget-boundary>summary{padding:16px 0;border-block:1px solid var(--san-rule);font-family:Georgia,serif;font-size:1rem}.v2-site .budget-boundary__body{padding:12px 0 2px;max-width:72ch}
.v2-site .policy-example-list{margin-top:24px;border-top:1px solid var(--san-rule)}.v2-site details.policy-example{margin:0;border-bottom:1px solid var(--san-rule)}.v2-site details.policy-example>summary{display:flex;justify-content:space-between;gap:24px;align-items:center;padding:20px 0;list-style:none;cursor:pointer}.v2-site details.policy-example>summary::-webkit-details-marker{display:none}.v2-site details.policy-example>summary span{display:grid;gap:5px}.v2-site details.policy-example>summary small{color:var(--san-muted);font:600 .68rem/1.4 Arial,sans-serif;letter-spacing:.06em;text-transform:uppercase}.v2-site details.policy-example>summary strong{font:500 clamp(1.05rem,1.8vw,1.35rem)/1.25 Georgia,serif}.v2-site details.policy-example>summary i{font-style:normal;transition:transform .18s ease}.v2-site details.policy-example[open]>summary i{transform:rotate(45deg)}.v2-site .policy-example__body{max-width:76ch;padding:0 0 24px}.v2-site .policy-example__body h4{margin:22px 0 4px;font-size:.83rem;text-transform:uppercase;letter-spacing:.055em}
.v2-site .paper-contents-disclosure{margin-block:46px;border-block:1px solid var(--san-rule)}.v2-site .paper-contents-disclosure>summary{padding:18px 0;font:500 1.1rem/1.4 Georgia,serif;cursor:pointer}.v2-site .paper-contents-disclosure .v2-paper-sections{margin:0 0 28px}.v2-site .reference-list article{border:0;border-top:1px solid var(--san-rule);border-radius:0;padding:20px 0;background:transparent}.v2-site .reference-controls{box-shadow:none;border-color:var(--san-rule)}.v2-site .v2-output-groups{gap:clamp(28px,4vw,56px)}.v2-site .v2-output-groups article{border-top:1px solid var(--san-rule);padding-top:18px}.v2-site .v2-footer{margin-top:clamp(66px,9vw,110px)}
@media(max-width:760px){.v2-site .v2-main{width:min(100% - 30px,1180px)}.v2-site .v2-header{width:100%;padding:10px 15px;align-items:center}.v2-site .v2-header nav{display:flex;overflow-x:auto;overscroll-behavior-inline:contain;white-space:nowrap;gap:18px;padding-bottom:3px}.v2-site .v2-wordmark small{display:none}.v2-site .v2-hero{padding-top:38px}.v2-site .v2-hero h1{font-size:clamp(2.25rem,12vw,3.1rem)}.v2-site .v2-hero-art figcaption{font-size:.73rem}.v2-site .v2-actions{display:grid;grid-template-columns:1fr}.v2-site .v2-parts--simple{gap:12px}.v2-site .v2-part-card{padding:20px}.v2-site .v2-page-lead h1{font-size:clamp(2.05rem,10vw,3rem)}.v2-site details.policy-example>summary{align-items:flex-start;padding:17px 0}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{scroll-behavior:auto!important;transition-duration:.01ms!important;animation-duration:.01ms!important;animation-iteration-count:1!important}}
''',
)

app_path = ROOT / "src/EditorialApp.tsx"
text = app_path.read_text(encoding="utf-8")
if 'sanitization.css' not in text:
    imports = list(re.finditer(r'^import .*?;\s*$', text, flags=re.M))
    position = imports[-1].end() if imports else 0
    text = text[:position] + '\nimport "./editorial/sanitization.css";' + text[position:]
write("src/EditorialApp.tsx", text)


# Search-engine and route hygiene.
write(
    "public/robots.txt",
    "User-agent: *\nAllow: /\nSitemap: https://miguelguerrero.eu/agencytransfer/sitemap.xml\n",
)
routes = [
    "",
    "research/",
    "research/part-i/",
    "research/part-iii/",
    "research/part-iv/",
    "paper/",
    "outputs/",
    "explainers/",
    "references/",
    "about/",
]
sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for route in routes:
    sitemap.append(f"  <url><loc>https://miguelguerrero.eu/agencytransfer/{route}</loc><lastmod>2026-09-03</lastmod></url>")
sitemap.append("</urlset>")
write("public/sitemap.xml", "\n".join(sitemap))


# Retire the old, unused hero materialisation pipeline.
package_path = ROOT / "package.json"
package = json.loads(package_path.read_text(encoding="utf-8"))
package.get("scripts", {}).pop("materialize:cde-rift", None)
for key, value in list(package.get("scripts", {}).items()):
    value = re.sub(r'\s*npm run materialize:cde-rift\s*&&\s*', "", value)
    value = re.sub(r'\s*&&\s*npm run materialize:cde-rift\s*', "", value)
    package["scripts"][key] = value
write("package.json", json.dumps(package, indent=2))

for workflow in (".github/workflows/deploy-pages.yml", ".github/workflows/evals-ci.yml"):
    target = ROOT / workflow
    content = target.read_text(encoding="utf-8")
    content = content.replace("dist/media/cde-rift-hero.webp", "dist/media/cde-gap3-hero-1672.webp")
    if "python scripts/audit-publication.py" not in content:
        anchor = "      - name: Assert programme output\n"
        if anchor in content:
            content = content.replace(
                anchor,
                "      - name: Audit public publication\n        run: python scripts/audit-publication.py\n" + anchor,
                1,
            )
        else:
            raise SystemExit(f"{workflow}: assertion anchor not found")
    content = content.replace(
        "          test -f dist/about/index.html\n",
        "          test -f dist/about/index.html\n          test -f dist/references/index.html\n          test -f dist/robots.txt\n          test -f dist/sitemap.xml\n",
    )
    write(workflow, content)

# Remove generated legacy hero files only after all source references are gone.
materializer = ROOT / "scripts/materialize-cde-rift.mjs"
candidates = [
    materializer,
    ROOT / "public/media/cde-rift-hero.png",
    ROOT / "public/media/cde-rift-hero.webp",
    ROOT / "src/assets/cde-rift-hero.base64",
    ROOT / "src/assets/cde-rift-hero.webp.base64",
]
if materializer.exists():
    source = materializer.read_text(encoding="utf-8")
    for value in re.findall(r'["\']([^"\']*(?:cde-rift-hero|base64)[^"\']*)["\']', source):
        candidate = ROOT / value
        if candidate.is_relative_to(ROOT):
            candidates.append(candidate)
for candidate in set(candidates):
    if candidate.exists() and candidate.is_file():
        name = candidate.name
        refs = []
        for other in ROOT.rglob("*"):
            if not other.is_file() or other == candidate or "node_modules" in other.parts or ".git" in other.parts:
                continue
            if other.suffix.lower() not in {".ts", ".tsx", ".js", ".mjs", ".json", ".md", ".yml", ".yaml", ".html", ".css", ".cff"}:
                continue
            try:
                other_text = other.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if name in other_text:
                refs.append(other.relative_to(ROOT).as_posix())
        refs = [ref for ref in refs if ref != ".github/workflows/deep-sanitization-source-once.yml"]
        if not refs:
            candidate.unlink()

# Remove the temporary Brazil pointer, not the documented unpublished scenario.
temporary = ROOT / "tmp/brazil2026-artifacts-20260824.md"
if temporary.exists() and re.search(r"tmpfiles|temporary|preview", temporary.read_text(encoding="utf-8", errors="ignore"), flags=re.I):
    temporary.unlink()
    try:
        temporary.parent.rmdir()
    except OSError:
        pass

manifest_path = ROOT / "programme/project-manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["programme"]["last_updated"] = "2026-09-03"
for artifact in manifest.get("artifacts", []):
    if artifact.get("id") == "brazil-2026-explainer" and str(artifact.get("repo_path", "")).startswith("tmp/"):
        artifact["repo_path"] = None
        artifact["publication_note"] = "Synthetic scenario retained as unpublished programme history; no temporary public host is listed."
write("programme/project-manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))


# Permanent built-site sanitation audit.
write(
    "scripts/audit-publication.py",
    r'''#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/"dist"
FORBIDDEN=("agencytransfer-controlled","tmpfiles.org","transfer.sh","file.io","BEGIN PRIVATE KEY")
ALLOWED_LARGE={".pdf",".xlsx",".parquet"}
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.h1=0;self.links=[];self.images=[];self.title=False;self.desc=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if "id" in a:self.ids.append(a["id"])
  if tag=="h1":self.h1+=1
  if tag=="a":self.links.append(a)
  if tag=="img":self.images.append(a)
  if tag=="title":self.title=True
  if tag=="meta" and a.get("name")=="description":self.desc=bool(a.get("content"))
def target(url):
 p=urlparse(url)
 if p.scheme or p.netloc or url.startswith(("#","mailto:","tel:","javascript:")):return None
 clean=p.path;base="/agencytransfer/"
 if clean.startswith(base):clean=clean[len(base):]
 elif clean.startswith("/"):return None
 path=DIST/clean
 if clean.endswith("/"):path=path/"index.html"
 elif not path.suffix:path=path/"index.html"
 return path
def main():
 errors=[];warnings=[];rows=[];hashes={}
 for path in DIST.rglob("*"):
  if not path.is_file():continue
  rel=path.relative_to(DIST).as_posix();raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();hashes.setdefault(digest,[]).append(rel)
  if len(raw)>3_000_000 and path.suffix.lower() not in ALLOWED_LARGE:warnings.append(f"large asset {rel}: {len(raw)}")
  if path.suffix.lower() in {".html",".js",".css",".json",".md",".txt",".xml"}:
   text=raw.decode("utf-8","replace")
   for token in FORBIDDEN:
    if token.lower() in text.lower():errors.append(f"forbidden public token {token}: {rel}")
  if path.suffix.lower()==".html":
   parser=Parser();parser.feed(raw.decode("utf-8","replace"))
   if parser.h1!=1:errors.append(f"{rel}: expected one h1, found {parser.h1}")
   if len(parser.ids)!=len(set(parser.ids)):errors.append(f"{rel}: duplicate id")
   if not parser.title or not parser.desc:errors.append(f"{rel}: missing title/description")
   for image in parser.images:
    if not image.get("alt") and image.get("role")!="presentation":errors.append(f"{rel}: image without alt")
    candidate=target(image.get("src",""))
    if candidate and not candidate.exists():errors.append(f"{rel}: missing image {image.get('src')}")
   for link in parser.links:
    candidate=target(link.get("href",""))
    if candidate and not candidate.exists():errors.append(f"{rel}: broken internal link {link.get('href')}")
    if link.get("target")=="_blank" and "noreferrer" not in link.get("rel",""):errors.append(f"{rel}: blank target without noreferrer")
   rows.append(rel)
 duplicates=[group for group in hashes.values() if len(group)>1 and not all(item.endswith("index.html") for item in group)]
 report={"status":"pass" if not errors else "fail","htmlPages":len(rows),"errors":errors,"warnings":warnings,"duplicateAssetGroups":duplicates}
 output=ROOT/"programme/reviews/20260903-deep-sanitization-audit.json";output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2))
 print(json.dumps({"status":report["status"],"htmlPages":len(rows),"errors":len(errors),"warnings":len(warnings),"duplicateGroups":len(duplicates)},indent=2))
 if errors:sys.exit(1)
if __name__=="__main__":main()
''',
)

# Browser acceptance script retained for reproducible review.
write(
    "scripts/review-sanitization.py",
    r'''#!/usr/bin/env python3
from __future__ import annotations
import json,os,pathlib,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/"sanitization-browser-review";BASE=os.environ.get("REVIEW_BASE","http://127.0.0.1:8765/agencytransfer/")
ROUTES=("","research/part-i/","research/part-iii/","research/part-iv/","paper/","references/","outputs/","explainers/","media/cde-rift-animation/","about/");WIDTHS=(1440,768,390,320)
def main():
 OUT.mkdir(exist_ok=True);proc=None
 if BASE.startswith("http://127.0.0.1"):
  server=ROOT/"_sanitization_preview"
  if server.exists():import shutil;shutil.rmtree(server)
  server.mkdir();(server/"agencytransfer").symlink_to(ROOT/"dist",target_is_directory=True)
  proc=subprocess.Popen(["python","-m","http.server","8765","--directory",str(server)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
 report={"base":BASE,"pages":[],"result":"pending"}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch()
   for width in WIDTHS:
    ctx=browser.new_context(viewport={"width":width,"height":1000 if width>=768 else 844},reduced_motion="reduce");page=ctx.new_page();errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
    for slug in ROUTES:
     response=page.goto(BASE+slug,wait_until="networkidle",timeout=30000);assert response and response.status==200,(slug,response.status if response else None)
     page.locator("h1").first.wait_for();assert page.locator("h1").count()==1,(slug,"h1");scroll=page.evaluate("document.documentElement.scrollWidth");assert scroll<=width+1,(slug,width,scroll)
     assert page.locator(".v2-header").count()==1 and page.locator(".v2-draftbar").count()==1,(slug,"shell")
     if slug=="":
      assert page.locator(".v2-parts--simple .v2-part-card").count()==4;assert page.locator(".publication-pending").count()==0;assert page.locator('a[href$="/registry/"]').first.get_attribute("target")=="_blank"
     if slug=="research/part-i/":
      assert page.locator("h1").inner_text()=="How far can an adversarial actor go with $10?";details=page.locator("details.budget-boundary");assert details.count()==1 and details.get_attribute("open") is None;details.locator("summary").click();assert details.get_attribute("open") is not None
     if slug=="research/part-iii/":assert page.locator(".v2-wide-figure").count()==0
     if slug=="research/part-iv/":
      assert "appears useful" in page.locator("h1").inner_text().lower();items=page.locator("details.policy-example");assert items.count()==6 and all(item.get_attribute("open") is None for item in items.all());items.first.locator("summary").click();assert items.first.get_attribute("open") is not None
     if slug=="paper/":assert page.locator("details.paper-contents-disclosure").count()==1 and page.locator("details.paper-contents-disclosure").get_attribute("open") is None
     if slug=="references/":assert page.locator("input[type=search]").count()==1 and "source record" in page.locator("main").inner_text().lower()
     if slug in ("explainers/","media/cde-rift-animation/"):assert page.locator("iframe").count()==1
     report["pages"].append({"path":slug,"width":width,"status":response.status,"scrollWidth":scroll})
     if width in (1440,390) and slug in ("","research/part-i/","research/part-iv/","paper/","references/","outputs/","explainers/"):
      name=(slug or "home").strip("/").replace("/","-");page.evaluate("window.scrollTo(0,0)");page.screenshot(path=str(OUT/f"{name}-{width}.png"),full_page=True)
    assert not errors,errors;ctx.close()
   browser.close();report["result"]="pass"
 except Exception as error:report["result"]="fail";report["error"]=repr(error);raise
 finally:
  (OUT/"report.json").write_text(json.dumps(report,indent=2))
  if proc:proc.terminate()
 print(json.dumps({"result":report["result"],"checks":len(report["pages"])},indent=2))
if __name__=="__main__":main()
''',
)

write(
    "programme/reviews/20260903-deep-sanitization.md",
    '''# Deep sanitization review — 3 September 2026

**Status:** working publication; editorial and asset sanitation only. No Part II Registry code, benchmark observations, incident denominators or policy-effect grades were changed.

## What was corrected

- Replaced the inaccurate “four audits” label with **four workstreams**.
- Kept the **$10** question and “Pretty far, actually” as the Part I hook; moved the full cost and evidence boundary into a later disclosure.
- Reduced Part I to two visible claims: what the pilot suggests and what it does not show.
- Removed the repeated CDE illustration from Part III. The primary illustration now has one main role on the homepage and one explanatory role in the guide.
- Softened Part IV from “what works” to **what appears useful**, and collapsed six long policy examples into readable evidence disclosures.
- Collapsed the paper’s detailed contents behind a single disclosure; the full PDF remains the source of record.
- Clarified that the references page is a **source record**, not a count of independently reviewed studies.
- Removed the unpublished poster/white-paper notice from the homepage; unavailable items remain only in Artifacts.

## Style and accessibility

- Normalised headline scale, line length, spacing, card height, rules and mobile navigation.
- Preserved Georgia-led editorial typography, warm paper background and restrained burgundy accent.
- Added consistent focus states and reduced-motion behaviour.
- Made policy evidence, paper contents and budget qualifications progressively disclosed rather than permanently expanded.
- Added `robots.txt` and `sitemap.xml`.

## Asset and publication hygiene

- Removed the obsolete generated hero-materialisation pipeline and old unused CDE hero copies where no remaining source reference existed.
- Removed the temporary Brazil preview-pointer file from the current tree; the unpublished scenario remains documented without an expiring public URL.
- Updated CI to assert the approved responsive hero rather than an obsolete asset.
- Added an automated built-site audit for internal links, duplicate IDs, page headings, image alt text, blank-target protection, forbidden private/temporary-host references and unexpectedly large assets.

## Retained intentionally

- The independent Registry, its Chart/Evidence/Testing pages, source code, data and existing mobile behaviour.
- The approved hero image.
- The v1.5 and historical v1.3 manuscript snapshots.
- Comprehensive source records and documented unresolved bibliographic entries.
- Backward-compatible explainer and legacy route URLs.

## Remaining known limitations

- Registry Evidence has a pre-existing narrow-screen overflow and remains outside this publication redesign.
- Poster, standalone white paper and the Brazil video do not yet have canonical public releases.
- The source library records varied review depth; inclusion is not full-text verification.
- GitHub Pages controls transport and platform headers; publication-level HTML cannot substitute for server-level security policy.
''',
)

changelog_path = ROOT / "CHANGELOG.md"
changelog = changelog_path.read_text(encoding="utf-8")
if "## Unreleased — 2026-09-03" not in changelog:
    entry = '''
## Unreleased — 2026-09-03

### Deep publication sanitization

- Simplified Part I, Part III, Part IV, the paper overview and artifact directory without changing empirical records.
- Kept the $10 hook while moving full cost and evidence qualifications later in the reading path.
- Normalised typography, spacing, disclosure patterns, focus states and mobile navigation.
- Removed obsolete generated hero assets and temporary preview pointers when unreferenced.
- Added a built-site audit, robots file, sitemap and a dated sanitation record.

'''
    position = changelog.find("\n## ")
    changelog = changelog[:position] + entry + changelog[position:] if position >= 0 else changelog + entry
    write("CHANGELOG.md", changelog)

print("Deep sanitization source changes staged.")
