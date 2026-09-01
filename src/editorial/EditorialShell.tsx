import { useEffect, type ReactNode } from "react";

export const BASE = import.meta.env.BASE_URL;
export const REPOSITORY_URL = "https://github.com/apolmig/agencytransfer";
export const LAB_URL = "https://agency-transfer-lab.miguelguerrero.eu";
export const REGISTRY_DATA_URL = "https://huggingface.co/datasets/apol/agency-transfer-benchmark";
export const ELECTION_INDEX_URL = "https://huggingface.co/datasets/apol/ai-election-manipulation-cases";
export const POLICY_ATLAS_URL = "https://huggingface.co/datasets/apol/agency-transfer-policy-atlas";
export const MANUEL_VIDEO_URL = "https://www.youtube.com/watch?v=ZTyWOhF7Pto";

export const route = (path = "") => `${BASE}${path.replace(/^\/+/, "")}`;
const asset = (path: string) => route(path);

export const RIFT_ANIMATION = asset("media/cde-rift-animation/index.html");
export const RIFT_IMAGE = asset("media/cde-rift-hero.png");

export const getPath = () => {
  const base = BASE.replace(/\/$/, "");
  let path = window.location.pathname;
  if (base && path.startsWith(base)) path = path.slice(base.length);
  return path.replace(/index\.html$/, "").replace(/^\/+|\/+$/g, "");
};

const metadata: Record<string, { title: string; description: string }> = {
  "": {
    title: "Harmful Manipulation and Election Security · Working Draft",
    description: "A draft research programme on frontier AI, harmful manipulation, election security, and the Capability–Deployment–Effect Gap.",
  },
  research: {
    title: "Research · Harmful Manipulation and Election Security",
    description: "Four linked audits of operations, evaluation, field evidence, and policy evidence.",
  },
  "research/part-i": {
    title: "Part I · How far can an adversarial actor go with $10? · Draft",
    description: "Author-reported low-cost sandbox planning, with explicit full-cost and evidence limits. Not a verified influence campaign.",
  },
  "research/part-iii": {
    title: "Part III · Field evidence · Harmful Manipulation and Election Security",
    description: "Documented influence attempts, harassment and confusion; bounded human evidence and unresolved electoral effects.",
  },
  "research/part-iv": {
    title: "Part IV · What works—and for whom? · Working Draft",
    description: "A source-linked review of 118 policy implementations: what specific controls change, whose agency they protect, and what remains untested.",
  },
  paper: {
    title: "Flagship Working Paper · Harmful Manipulation and Election Security",
    description: "Web overview and full v1.3 working paper: The Capability–Deployment–Effect Gap, with the 1 September policy review.",
  },
  outputs: {
    title: "Artifacts · Harmful Manipulation and Election Security",
    description: "Working paper, visual overview, registry, evidence index, policy atlas, explainers, and research tools.",
  },
  explainers: {
    title: "Explainers · The Capability–Deployment–Effect Gap",
    description: "The animated CDE Rift and bounded synthetic mechanism explainers.",
  },
  about: {
    title: "About · Harmful Manipulation and Election Security",
    description: "Scope, status, evidence policy, author, and responsible release.",
  },
  updates: {
    title: "Draft log · Harmful Manipulation and Election Security",
    description: "Material changes to the draft research programme and its public artifacts.",
  },
};

export function useMetadata(path: string) {
  useEffect(() => {
    const entry = metadata[path] ?? metadata[""];
    const pageTitle = /draft/i.test(entry.title) ? entry.title : `${entry.title} · Draft`;
    document.title = pageTitle;
    const description = document.querySelector<HTMLMetaElement>('meta[name="description"]');
    if (description) description.content = `${entry.description} Research in progress; programme findings and recommendations are provisional, not peer reviewed.`;
    const canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (canonical) canonical.href = `https://miguelguerrero.eu/agencytransfer/${path ? `${path}/` : ""}`;
    const ogTitle = document.querySelector<HTMLMetaElement>('meta[property="og:title"]');
    if (ogTitle) ogTitle.content = pageTitle;
    const ogDescription = document.querySelector<HTMLMetaElement>('meta[property="og:description"]');
    if (ogDescription) ogDescription.content = `${entry.description} Working draft; provisional programme findings.`;
    const ogUrl = document.querySelector<HTMLMetaElement>('meta[property="og:url"]');
    if (ogUrl) ogUrl.content = `https://miguelguerrero.eu/agencytransfer/${path ? `${path}/` : ""}`;
    document.body.classList.add("editorial-v2-active");
    return () => document.body.classList.remove("editorial-v2-active");
  }, [path]);
}

const activeSection = (path: string) => {
  if (!path) return "programme";
  if (path === "research" || path.startsWith("research/")) return "research";
  if (path === "outputs" || path === "explainers" || path === "paper") return "artifacts";
  return "about";
};

export function SiteHeader({ path }: { path: string }) {
  const active = activeSection(path);
  const links = [
    ["programme", "Programme", route()],
    ["research", "Research", route("research/")],
    ["registry", "Registry", route("registry/")],
    ["lab", "Lab", LAB_URL],
    ["artifacts", "Artifacts", route("outputs/")],
    ["about", "About", route("about/")],
  ] as const;

  return (
    <header className="v2-header">
      <a className="v2-wordmark" href={route()} aria-label="Agency Transfer Research Programme home">
        <span className="v2-mark" aria-hidden="true">✦</span>
        <span><strong>Agency Transfer</strong><small>Research Programme</small></span>
      </a>
      <nav aria-label="Primary navigation">
        {links.map(([id, label, href]) => {
          const external = /^https?:\/\//.test(href);
          return (
            <a
              key={id}
              href={href}
              aria-current={active === id ? "page" : undefined}
              target={external ? "_blank" : undefined}
              rel={external ? "noreferrer" : undefined}
            >
              {label}
            </a>
          );
        })}
      </nav>
    </header>
  );
}

export function DraftBar() {
  return (
    <div className="v2-draftbar" role="status">
      <div><span aria-hidden="true" /><strong>Draft · work in progress</strong><p>All programme results and recommendations are provisional · not peer reviewed. <a href={route("about/#evidence-status")}>Evidence key</a></p></div>
      <time dateTime="2026-09-01">Updated: 1 September 2026</time>
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="v2-footer">
      <div className="v2-footer-brand">
        <span className="v2-mark" aria-hidden="true">✦</span>
        <div><strong>Agency Transfer Research Programme</strong><p>Frontier AI, harmful manipulation, election security, and the Capability–Deployment–Effect Gap.</p></div>
      </div>
      <div className="v2-footer-links">
        <a href={route("paper/")}>Working paper</a>
        <a href={route("registry/")}>Registry</a>
        <a href={route("outputs/")}>Artifacts</a>
        <a href={`${REPOSITORY_URL}/blob/main/RESPONSIBLE_RELEASE.md`} target="_blank" rel="noreferrer">Responsible release ↗</a>
        <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">Source ↗</a>
      </div>
      <p className="v2-footer-note">Draft research by Miguel Guerrero · ERA:AI Summer Research Fellowship, Cambridge · 2026. Programme results, interpretations and recommendations remain provisional; no independent replication.</p>
    </footer>
  );
}

export function DraftBoundary({ children }: { children: ReactNode }) {
  return <aside className="v2-boundary"><strong>Provisional claim boundary</strong><p>{children}</p></aside>;
}

export function TextLink({ href, children, external = false }: { href: string; children: ReactNode; external?: boolean }) {
  return <a className="v2-text-link" href={href} target={external ? "_blank" : undefined} rel={external ? "noreferrer" : undefined}>{children}<span aria-hidden="true">→</span></a>;
}

export function PageLead({ eyebrow, title, deck, children }: { eyebrow: string; title: string; deck: string; children?: ReactNode }) {
  return (
    <section className="v2-page-lead">
      <p className="v2-eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p className="v2-deck">{deck}</p>
      {children}
    </section>
  );
}
