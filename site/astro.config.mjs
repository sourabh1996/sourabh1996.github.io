import { defineConfig } from "astro/config";

// SITE_URL / BASE_PATH are set by the GitHub Pages workflow.
// For a <username>.github.io repo the base stays "/".
export default defineConfig({
  site: process.env.SITE_URL || "https://example.github.io",
  base: process.env.BASE_PATH || "/",
  trailingSlash: "always",
  markdown: { shikiConfig: { theme: "github-dark" } },
});
