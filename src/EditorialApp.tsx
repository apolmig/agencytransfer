import App from "./App";
import { DraftBar, SiteFooter, SiteHeader, getPath, useMetadata } from "./editorial/EditorialShell";
import { PartIILead, renderEditorialPage } from "./editorial/EditorialPages";

function delegatedToExistingApp(path: string) {
  return path === "research/part-ii" || path === "research/part-ii/evidence" || path === "research/part-ii/testing" || path === "evidence" || path === "testing";
}

export default function EditorialApp() {
  const path = getPath();
  useMetadata(path);
  const delegated = delegatedToExistingApp(path);
  return (
    <div className="v2-site">
      <a className="v2-skip-link" href="#main-content">Skip to content</a>
      <SiteHeader path={path} />
      <DraftBar />
      {path === "research/part-ii" ? <PartIILead /> : null}
      {delegated ? (
        <div className={`legacy-app-wrap${path === "research/part-ii" ? " legacy-app-wrap--part-ii" : ""}`}><App /></div>
      ) : renderEditorialPage(path)}
      <SiteFooter />
    </div>
  );
}
