import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const entry = (path: string) => new URL(path, import.meta.url).pathname;

export default defineConfig({
  plugins: [react()],
  base: "/agencytransfer/",
  server: {
    host: "0.0.0.0",
    port: 4173,
    allowedHosts: ["terminal.local"],
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      input: {
        home: entry("./index.html"),
        research: entry("./research/index.html"),
        partI: entry("./research/part-i/index.html"),
        partII: entry("./research/part-ii/index.html"),
        partIIEvidence: entry("./research/part-ii/evidence/index.html"),
        partIITesting: entry("./research/part-ii/testing/index.html"),
        partIII: entry("./research/part-iii/index.html"),
        partIV: entry("./research/part-iv/index.html"),
        registry: entry("./registry/index.html"),
        registryEvidence: entry("./registry/evidence/index.html"),
        registryTesting: entry("./registry/testing/index.html"),
        references: entry("./references/index.html"),
        paper: entry("./paper/index.html"),
        outputs: entry("./outputs/index.html"),
        explainers: entry("./explainers/index.html"),
        updates: entry("./updates/index.html"),
        about: entry("./about/index.html"),
        legacyEvidence: entry("./evidence/index.html"),
        legacyTesting: entry("./testing/index.html"),
      },
    },
  },
});
