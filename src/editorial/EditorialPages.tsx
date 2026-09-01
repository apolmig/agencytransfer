import { ReferencesPage } from "./ReferencesPage";
import { HomePage, PartIPage, ResearchPage } from "./ProgrammePages";
import { PartIIIPage, PartIVPage } from "./EvidencePages";
import { AboutPage, ExplainersPage, OutputsPage, PaperPage, UpdatesPage } from "./ResourcePages";

export function renderEditorialPage(path: string) {
  switch (path) {
    case "research": return <ResearchPage />;
    case "research/part-i": return <PartIPage />;
    case "research/part-iii": return <PartIIIPage />;
    case "research/part-iv": return <PartIVPage />;
    case "references": return <ReferencesPage />;
    case "paper": return <PaperPage />;
    case "outputs": return <OutputsPage />;
    case "explainers": return <ExplainersPage />;
    case "updates": return <UpdatesPage />;
    case "about": return <AboutPage />;
    default: return <HomePage />;
  }
}
