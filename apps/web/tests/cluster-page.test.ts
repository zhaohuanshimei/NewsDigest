import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");
const outDir = "dist-cluster-success";

describe("cluster detail page success build", () => {
  it("renders cluster detail when the success override is enabled", () => {
    rmSync(resolve(appDir, outDir), { force: true, recursive: true });

    execSync(`npm run build -- --outDir ${outDir}`, {
      cwd: appDir,
      env: {
        ...process.env,
        PUBLIC_CLUSTER_STATE: "success"
      },
      stdio: "pipe"
    });

    const html = readFileSync(
      resolve(appDir, outDir, "clusters/cluster-ai-chip-001/index.html"),
      "utf8"
    );

    expect(html).toContain("technology");
    expect(html).toContain("AI 芯片与模型基础设施继续升温");
    expect(html).toContain("3 sources");
    expect(html).toContain("2026-06-24");
  }, 60000);
});
