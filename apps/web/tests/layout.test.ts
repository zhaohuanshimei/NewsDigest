import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");
const outDir = "dist-layout";

describe("layout structure", () => {
  it("renders header, navigation, and footer on homepage", () => {
    rmSync(resolve(appDir, outDir), { force: true, recursive: true });

    execSync(`npm run build -- --outDir ${outDir}`, {
      cwd: appDir,
      env: {
        ...process.env,
        PUBLIC_DIGEST_STATE: "success"
      },
      stdio: "pipe"
    });

    const html = readFileSync(resolve(appDir, outDir, "index.html"), "utf8");

    // Header
    expect(html).toContain("News Digest");
    expect(html).toContain("site-header");

    // Navigation
    expect(html).toContain("site-nav");
    expect(html).toContain("Main navigation");
    expect(html).toMatch(/href="\/"/);
    expect(html).toMatch(/href="\/archive"/);
    expect(html).toMatch(/href="\/rss"/);
    expect(html).toMatch(/href="\/about"/);

    // Footer
    expect(html).toContain("site-footer");
    expect(html).toContain("&copy;");
    expect(html).toContain(new Date().getFullYear().toString());
  }, 20_000);

  it("renders layout on archive page", () => {
    const html = readFileSync(resolve(appDir, outDir, "archive", "index.html"), "utf8");

    expect(html).toContain("site-header");
    expect(html).toContain("site-nav");
    expect(html).toContain("site-footer");
    expect(html).toMatch(/href="\/archive"/);
    expect(html).toContain("is-active");
  });

  it("includes SEO meta tags", () => {
    const html = readFileSync(resolve(appDir, outDir, "index.html"), "utf8");

    expect(html).toContain("<meta name=\"description\"");
    expect(html).toContain("<meta property=\"og:title\"");
    expect(html).toContain("<meta property=\"og:description\"");
    expect(html).toContain("<meta name=\"twitter:card\"");
    expect(html).toContain("<link rel=\"canonical\"");
  });
});
