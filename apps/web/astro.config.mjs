import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://news.maczhao.com",
  integrations: [sitemap()],
  server: {
    host: true,
    port: 4321
  }
});
