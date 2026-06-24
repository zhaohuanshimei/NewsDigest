import { describe, expect, it, vi } from "vitest";

import { loadHomepageDigest } from "../../src/lib/content/getLatestDigest";

describe("loadHomepageDigest", () => {
  it("returns a success state when the mock success override is enabled", async () => {
    const result = await loadHomepageDigest({ stateOverride: "success" });

    expect(result.kind).toBe("success");
    if (result.kind !== "success") return;

    expect(result.digest.date).toBe("2026-06-24");
    expect(result.digest.entries[0]?.headline).toBe("AI 芯片与模型基础设施继续升温");
  });

  it("returns an empty state when the seam is told to simulate no digest", async () => {
    const result = await loadHomepageDigest({ stateOverride: "empty" });

    expect(result).toEqual({ kind: "empty" });
  });

  it("returns an error state when the seam is told to simulate a failure", async () => {
    const result = await loadHomepageDigest({ stateOverride: "error" });

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load latest digest."
    });
  });

  it("fetches the latest digest from the API when no override is present", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        date: "2026-06-25",
        published_at: "2026-06-25T09:00:00Z",
        entries: [
          {
            cluster_id: "cluster-markets-001",
            rank: 1,
            category: "business",
            headline: "Global markets react to policy signals",
            summary: "Investors recalibrated expectations after the latest central bank remarks.",
            source_count: 4
          }
        ]
      })
    });

    const result = await loadHomepageDigest({
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(fetchImpl).toHaveBeenCalledWith(
      "http://127.0.0.1:8001/api/v1/digests/latest",
      expect.objectContaining({
        headers: {
          accept: "application/json"
        }
      })
    );
    expect(result.kind).toBe("success");
    if (result.kind !== "success") return;

    expect(result.digest.date).toBe("2026-06-25");
    expect(result.digest.entries[0]?.source_count).toBe(4);
  });

  it("maps a 404 latest-digest response to the empty state", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: false,
      status: 404
    });

    const result = await loadHomepageDigest({
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(result).toEqual({ kind: "empty" });
  });

  it("maps network failures to the existing error state", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("connection refused"));

    const result = await loadHomepageDigest({
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load latest digest."
    });
  });
});
