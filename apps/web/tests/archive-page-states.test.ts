import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");

function buildArchiveAndRead(state: "empty" | "error"): string {
  const outDir = `dist-archive-${state}`;

  rmSync(resolve(appDir, outDir), { force: true, recursive: true });

  execSync(`npm run build -- --outDir ${outDir}`, {
    cwd: appDir,
    env: {
      ...process.env,
      PUBLIC_ARCHIVE_STATE: state
    },
    stdio: "pipe"
  });

  return readFileSync(resolve(appDir, outDir, "archive/index.html"), "utf8");
}

describe("archive page alternate states", () => {
  it("renders an empty-state message", () => {
    const html = buildArchiveAndRead("empty");

    expect(html).toContain("No digest published yet.");
  }, 20_000);

  it("renders an error-state message", () => {
    const html = buildArchiveAndRead("error");

    expect(html).toContain("Unable to load archive dates.");
  }, 20_000);
});
