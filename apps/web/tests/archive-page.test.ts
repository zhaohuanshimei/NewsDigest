import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");
const outDir = "dist-archive-success";

describe("archive page success build", () => {
  it("renders archive dates when the success override is enabled", () => {
    rmSync(resolve(appDir, outDir), { force: true, recursive: true });

    execSync(`npm run build -- --outDir ${outDir}`, {
      cwd: appDir,
      env: {
        ...process.env,
        PUBLIC_ARCHIVE_STATE: "success"
      },
      stdio: "pipe"
    });

    const html = readFileSync(resolve(appDir, outDir, "archive/index.html"), "utf8");

    expect(html).toContain("Archive");
    expect(html).toContain("2026-06-24");
    expect(html).toContain("2026-06-23");
  }, 20_000);
});
