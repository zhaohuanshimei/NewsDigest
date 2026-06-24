import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");

function buildAndRead(state: "empty" | "error"): string {
  const outDir = `dist-${state}`;

  rmSync(resolve(appDir, outDir), { force: true, recursive: true });

  execSync(`npm run build -- --outDir ${outDir}`, {
    cwd: appDir,
    env: {
      ...process.env,
      PUBLIC_DIGEST_STATE: state
    },
    stdio: "pipe"
  });

  return readFileSync(resolve(appDir, outDir, "index.html"), "utf8");
}

describe("homepage alternate states", () => {
  it("renders an empty-state message", () => {
    const html = buildAndRead("empty");

    expect(html).toContain("No digest published yet.");
  });

  it("renders an error-state message", () => {
    const html = buildAndRead("error");

    expect(html).toContain("Latest digest is temporarily unavailable.");
  });
});
