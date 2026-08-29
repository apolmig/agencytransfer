import LegacyRegistryApp from "./LegacyRegistryApp";
import { DraftBar, SiteFooter, SiteHeader, getPath, useMetadata } from "./editorial/EditorialShell";
import { renderEditorialPage } from "./editorial/EditorialPages";

function isRegistryPath(path: string) {
  return path === "registry"
    || path === "registry/evidence"
    || path === "registry/testing"
    || path === "research/part-ii"
    || path === "research/part-ii/evidence"
    || path === "research/part-ii/testing"
    || path === "evidence"
    || path === "testing";
}

function EditorialProgramme({ path }: { path: string }) {
  useMetadata(path);
  return (
    <div className="v2-site">
      <a className="v2-skip-link" href="#main-content">Skip to content</a>
      <SiteHeader path={path} />
      <DraftBar />
      {renderEditorialPage(path)}
      <SiteFooter />
    </div>
  );
}

export default function EditorialApp() {
  const path = getPath();
  if (isRegistryPath(path)) return <LegacyRegistryApp />;
  return <EditorialProgramme path={path} />;
}
