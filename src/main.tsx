import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import EditorialApp from "./EditorialApp";
import "./styles.css";
import "./programme.css";
import "./programme-overrides.css";
import "./editorial-v2.css";
import "./editorial-v2-visuals.css";
import "./simple-repository.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <EditorialApp />
  </StrictMode>,
);
