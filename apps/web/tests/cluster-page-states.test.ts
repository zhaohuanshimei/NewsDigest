import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");

function buildClusterAndRead(state: "not-found" | "error"): string {
  const outDir = `dist-cluster-${state}`;

  rmSync(resolve(appDir, outDir), { force: true, recursive: true });

  execSync(`npm run build -- --outDir ${outDir}`, {
    cwd: appDir,
    env: {
      ...process.env,
      PUBLIC_CLUSTER_STATE: state
    },
    stdio: "pipe"
  });

  return readFileSync(
    resolve(appDir, outDir, "clusters/cluster-ai-chip-001/index.html"),
    "utf8"
  );
}

describe("cluster detail page alternate states", () => {
  it("renders a not-found message", () => {
    const html = buildClusterAndRead("not-found");

    expect(html).toContain("This cluster is not available.");
  }, 60000);

  it("renders an error-state message", () => {
    const html = buildClusterAndRead("error");

    expect(html).toContain("Unable to load this cluster.");
  }, 60000);
});
