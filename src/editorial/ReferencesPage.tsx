import { useEffect, useMemo, useRef, useState } from "react";
import { PageLead, route } from "./EditorialShell";
import "./publication-polish.css";

type EntrySource = { collection: string; locator: string; title: string; authors: string; year: string; url: string; recordedStatus: string; note: string; boundary: string };
type Reference = { id: string; title: string; authors: string; year: string; url: string; alternateUrls: string[]; category: string; scope: string; parts: string[]; collections: string[]; recordedStatus: string; citations: string[]; note: string; boundary: string; flags: string[]; provenance: EntrySource[]; linkCheck: { status: string; checkedAt: string | null; httpStatus?: number; finalUrl?: string }; metadataNote?: string };
type Collection = { id: string; label: string; date: string; kind: string; recordCount: number };
type Library = { version: string; manuscriptVersion: string; scopeNote: string; collections: Collection[]; records: Reference[]; counts: { records: number; sourceEntries: number; flagshipCitations: number; flagshipRecords: number } };
const PAGE_SIZE = 25;
const normalise = (s: string) => s.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
const initialParams = () => new URLSearchParams(window.location.search);
const clearHash = () => { if (location.hash) history.replaceState(null, "", location.pathname + location.search); };
const publicUrl = (url: string) => /^https?:\/\//i.test(url);

export function ReferencesPage() {
  const [library, setLibrary] = useState<Library | null>(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(() => initialParams().get("q") ?? "");
  const [scope, setScope] = useState(() => initialParams().get("scope") ?? "all");
  const [collection, setCollection] = useState(() => initialParams().get("collection") ?? "all");
  const [page, setPage] = useState(1);
  const results = useRef<HTMLElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch(route("research/references.json"), { signal: controller.signal })
      .then(r => { if (!r.ok) throw new Error("The source library could not be loaded."); return r.json() as Promise<Library>; })
      .then(setLibrary).catch(e => { if (e.name !== "AbortError") setError("The interactive library could not load. The full plain-text bibliography is still available below."); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const params = new URLSearchParams();
    if (query.trim()) params.set("q", query.trim());
    if (scope !== "all") params.set("scope", scope);
    if (collection !== "all") params.set("collection", collection);
    const qs = params.toString();
    history.replaceState(null, "", `${location.pathname}${qs ? `?${qs}` : ""}${location.hash}`);
    setPage(1);
  }, [query, scope, collection]);
  useEffect(() => {
    const restore = () => { const p = initialParams(); setQuery(p.get("q") ?? ""); setScope(p.get("scope") ?? "all"); setCollection(p.get("collection") ?? "all"); };
    addEventListener("popstate", restore); return () => removeEventListener("popstate", restore);
  }, []);
  const indexed = useMemo(() => (library?.records ?? []).map(r => ({ record: r, text: normalise([r.title, r.authors, r.year, r.category, r.recordedStatus, r.note, ...r.provenance.map(p => `${p.title} ${p.authors}`)].join(" ")) })), [library]);
  const filtered = useMemo(() => {
    const words = normalise(query).trim().split(/\s+/).filter(Boolean);
    return indexed.filter(({ record: r, text }) => (scope === "all" || (scope === "flagship" ? r.scope === "flagship" : r.scope !== "flagship")) && (collection === "all" || r.collections.includes(collection)) && words.every(w => text.includes(w))).map(r => r.record);
  }, [indexed, query, scope, collection]);
  useEffect(() => {
    const openHash = () => {
      const id = decodeURIComponent(location.hash.slice(1));
      if (!id.startsWith("ref-") || !library) return;
      let index = filtered.findIndex(r => r.id === id);
      if (index < 0) { if (library.records.some(r => r.id === id)) { setQuery(""); setScope("all"); setCollection("all"); } return; }
      setPage(Math.floor(index / PAGE_SIZE) + 1);
      setTimeout(() => { const target = document.getElementById(id); target?.scrollIntoView({ block: "start" }); target?.focus({ preventScroll: true }); }, 80);
    };
    openHash(); addEventListener("hashchange", openHash); return () => removeEventListener("hashchange", openHash);
  }, [library, filtered]);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pages);
  const visible = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  const changePage = (n: number) => { history.replaceState(null, "", location.pathname + location.search); setPage(n); results.current?.focus({ preventScroll: true }); results.current?.scrollIntoView({ block: "start" }); };
  const reset = () => { history.replaceState(null, "", location.pathname); setQuery(""); setScope("all"); setCollection("all"); setPage(1); };
  const label = (id: string) => library?.collections.find(c => c.id === id)?.label ?? id;
  return <main id="main-content" className="v2-main references-page">
    <PageLead eyebrow="References & source library" title="The reading behind the research" deck="The flagship bibliography and the wider sources reviewed, registered or considered across the programme. Inclusion is not endorsement, independent verification or proof of an effect." />
    <p className="reference-scope">Manuscript v{library?.manuscriptVersion ?? "1.5"} · Source snapshot: 1 September 2026. {library?.scopeNote}</p>
    <div className="reference-downloads"><a href={route("research/references.html")} target="_blank" rel="noopener noreferrer">Read the full bibliography</a><a href={route("research/references.json")} download>Download source index · JSON</a></div>
    <section className="reference-search" aria-label="Find references">
      <div className="reference-tabs" role="group" aria-label="Reference scope">
        {[["all", "All sources"], ["flagship", "Cited in the flagship"], ["wider", "Wider reading & records"]].map(([id, title]) => <button key={id} type="button" aria-pressed={scope === id} onClick={() => { clearHash(); setScope(id); }}>{title}</button>)}
      </div>
      <div className="reference-fields"><label>Search by title, author or subject<input type="search" value={query} onChange={e => { clearHash(); setQuery(e.target.value); }} placeholder="For example: persuasion, Salvi, provenance…" /></label><label>Source collection<select value={collection} onChange={e => { clearHash(); setCollection(e.target.value); }}><option value="all">All collections</option>{library?.collections.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}</select></label><button type="button" onClick={reset}>Clear filters</button></div>
    </section>
    {error ? <p role="alert">{error}</p> : null}
    {!library && !error ? <p role="status">Loading references…</p> : null}
    {library ? <>
      <p className="reference-count" role="status">{filtered.length} source records{query || scope !== "all" || collection !== "all" ? ` matching these filters, from ${library.counts.records} in the library` : ` · ${library.counts.flagshipCitations} citations in the current flagship`}. Alphabetical by recorded author or institution.</p>
      <section ref={results} tabIndex={-1} className="reference-results" aria-label="Reference results">
        {!filtered.length ? <p>No matching source. Try a shorter title or another spelling, or <button type="button" className="plain-button" onClick={reset}>clear the filters</button>.</p> : <ol start={(currentPage - 1) * PAGE_SIZE + 1}>{visible.map(r => <li key={r.id} id={r.id} tabIndex={-1}>
          <div className="reference-meta"><span>{r.scope === "flagship" ? "Cited in the flagship" : r.scope === "review" ? "In a review record" : "Registered / considered"}</span><span>{r.category}</span></div>
          <h2>{publicUrl(r.url) ? <a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}<span className="sr-only"> (source, opens a new tab)</span></a> : r.title}</h2>
          <p className="reference-author">{r.authors || "Author not specified in the source record"}{r.year ? ` · ${r.year}` : " · Date not recorded"}</p>
          {r.citations.length ? <p className="reference-citation">{r.citations[0].replace(/https?:\/\/\S+/g, "").trim()}</p> : r.note && !/^(URL recorded|Claim checked|Primary abstract|Abstract|Full text)/i.test(r.note) ? <p className="reference-context">{r.note}</p> : null}
          <p className="reference-status">{r.recordedStatus}{!r.url ? r.linkCheck.status === "identity_mismatch" ? " · Source identity unresolved" : " · No public release linked in the manuscript" : r.linkCheck.status === "not_found" ? " · Recorded link did not resolve in the latest check" : ["access_limited", "unavailable"].includes(r.linkCheck.status) ? " · Automated access could not be confirmed" : ""}</p>
          {r.metadataNote ? <p className="reference-status">{r.metadataNote}</p> : null}
          <details><summary>Context, limits and source record</summary>
            {r.boundary ? <p><strong>Recorded limitation.</strong> {r.boundary}</p> : <p>No source-specific effect appraisal is added here. Consult the original source and programme record before relying on a claim.</p>}
            <p>Collection membership records how this source entered the programme. It does not establish that every page was read or every finding independently checked.</p>
            <ul>{r.provenance.map((p, i) => <li key={`${p.collection}-${i}`}><strong>{label(p.collection)}</strong> · {p.locator}<br />{p.title}{p.recordedStatus ? ` — ${p.recordedStatus}` : ""}{p.note ? <p>{p.note}</p> : null}</li>)}</ul>
            {r.alternateUrls.length ? <p>Other recorded versions: {r.alternateUrls.map((url, i) => <span key={url}>{i ? " · " : ""}<a href={url} target="_blank" rel="noopener noreferrer">Source {i + 2}</a></span>)}</p> : null}
            {r.url ? <p>Link check: {r.linkCheck.status.replaceAll("_", " ")}{r.linkCheck.checkedAt ? `, ${r.linkCheck.checkedAt}` : ""}. Reachability is not scientific verification.</p> : null}
            <a href={`#${r.id}`} aria-label={`Permanent link to ${r.title}`}>Link to this entry</a>
          </details>
        </li>)}</ol>}
      </section>
      {pages > 1 ? <nav className="reference-pagination" aria-label="Reference pages"><button type="button" disabled={currentPage === 1} onClick={() => changePage(currentPage - 1)}>Previous</button><span>Page {currentPage} of {pages}</span><button type="button" disabled={currentPage === pages} onClick={() => changePage(currentPage + 1)}>Next</button></nav> : null}
      <details className="reference-method"><summary>What is included, and how duplicates are handled</summary><p>{library.counts.sourceEntries} recorded entries were brought together into {library.counts.records} source records. Exact identifiers and matching titles join repeat entries; original titles, versions and collection locators remain accessible. Corrections and different editions are not treated as independent replication.</p><p>The main citation follows the current manuscript where available. Broader records retain their recorded source status, which may be incomplete or historical. Provider affiliation, peer review and evidence strength are separate questions.</p><ul>{library.collections.map(c => <li key={c.id}>{c.label} · {c.date} · {c.recordCount} input entries</li>)}</ul><p>Unlinked draft modules and proposed controls are not counted as literature. The manuscript’s five unpublished programme records are retained and clearly marked. No private folders or raw operational evidence are linked.</p></details>
    </> : null}
  </main>;
}
