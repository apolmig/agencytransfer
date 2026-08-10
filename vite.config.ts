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
        evidence: entry("./evidence/index.html"),
        testing: entry("./testing/index.html"),
      },
    },
  },
});
