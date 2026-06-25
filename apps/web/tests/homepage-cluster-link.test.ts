import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");
const outDir = "dist-home-cluster-link";

describe("homepage cluster link build", () => {
  it("links the latest digest entry to its cluster detail page", () => {
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

    expect(html).toContain('href="/clusters/cluster-ai-chip-001"');
  }, 60000);
});
