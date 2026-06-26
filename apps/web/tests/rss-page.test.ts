import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");
const outDir = "dist-rss";

describe("rss page build", () => {
  it("renders the RSS subscription page with feed link and layout", () => {
    rmSync(resolve(appDir, outDir), { force: true, recursive: true });

    execSync(`npm run build -- --outDir ${outDir}`, {
      cwd: appDir,
      env: {
        ...process.env,
        PUBLIC_DIGEST_STATE: "success"
      },
      stdio: "pipe"
    });

    const html = readFileSync(resolve(appDir, outDir, "rss/index.html"), "utf8");

    // Page heading
    expect(html).toContain("RSS 订阅");

    // Feed link
    expect(html).toContain('href="/feed.xml"');

    // Layout elements (consistent with layout.test.ts)
    expect(html).toContain("site-header");
    expect(html).toContain("site-nav");
    expect(html).toContain("site-footer");

    // RSS usage instructions
    expect(html).toContain("RSS 阅读器");
    expect(html).toContain("Feedly");
    expect(html).toContain("NetNewsWire");
  }, 20_000);
});
