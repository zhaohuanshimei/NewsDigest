import { describe, expect, it } from "vitest";

import { loadHomepageDigest } from "../../src/lib/content/getLatestDigest";

describe("loadHomepageDigest", () => {
  it("returns a success state with the latest digest contract", async () => {
    const result = await loadHomepageDigest("success");

    expect(result.kind).toBe("success");
    if (result.kind !== "success") return;

    expect(result.digest.date).toBe("2026-06-24");
    expect(result.digest.entries[0]?.headline).toBe("AI 芯片与模型基础设施继续升温");
  });

  it("returns an empty state when the seam is told to simulate no digest", async () => {
    const result = await loadHomepageDigest("empty");

    expect(result).toEqual({ kind: "empty" });
  });

  it("returns an error state when the seam is told to simulate a failure", async () => {
    const result = await loadHomepageDigest("error");

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load latest digest."
    });
  });
});
