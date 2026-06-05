import { defineConfig } from "vitest/config";
import path from "path";
import react from "@vitejs/plugin-react";

const ROOT = __dirname;

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
    css: true,
    // Exclude e2e tests (they belong to Playwright)
    exclude: ["e2e/**", "node_modules/**"],
    // Dedupe react to avoid multiple copies
    server: {
      deps: {
        inline: ["react", "react-dom"],
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(ROOT, "./src"),
    },
    // Force all react and react-dom imports to resolve from the same copy
    dedupe: ["react", "react-dom"],
  },
});
