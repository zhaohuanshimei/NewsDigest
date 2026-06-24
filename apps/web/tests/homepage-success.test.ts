import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");

describe("homepage success build", () => {
  it("renders the latest digest headline and metadata", () => {
    execSync("npm run build", {
      cwd: appDir,
      stdio: "pipe"
    });

    const html = readFileSync(resolve(appDir, "dist/index.html"), "utf8");

    expect(html).toContain("AI 芯片与模型基础设施继续升温");
    expect(html).toContain("2026-06-24");
    expect(html).toContain("3 sources");
  });
});
