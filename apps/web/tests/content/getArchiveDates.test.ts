import { describe, expect, it, vi } from "vitest";

import { loadArchiveDates } from "../../src/lib/content/getArchiveDates";

describe("loadArchiveDates", () => {
  it("returns a success state when the archive success override is enabled", async () => {
    const result = await loadArchiveDates({ stateOverride: "success" });

    expect(result).toEqual({
      kind: "success",
      dates: ["2026-06-24", "2026-06-23", "2026-06-22"]
    });
  });

  it("returns an empty state when the seam is told to simulate no archive dates", async () => {
    const result = await loadArchiveDates({ stateOverride: "empty" });

    expect(result).toEqual({ kind: "empty" });
  });

  it("returns an error state when the seam is told to simulate a failure", async () => {
    const result = await loadArchiveDates({ stateOverride: "error" });

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load archive dates."
    });
  });

  it("fetches archive dates from the real API when no override is present", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        dates: ["2026-06-24", "2026-06-23"]
      })
    });

    const result = await loadArchiveDates({
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(fetchImpl).toHaveBeenCalledWith(
      "http://127.0.0.1:8001/api/v1/archive/dates",
      expect.objectContaining({
        headers: {
          accept: "application/json"
        }
      })
    );
    expect(result).toEqual({
      kind: "success",
      dates: ["2026-06-24", "2026-06-23"]
    });
  });

  it("maps an empty archive list response to the empty state", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        dates: []
      })
    });

    const result = await loadArchiveDates({
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(result).toEqual({ kind: "empty" });
  });

  it("maps network failures to the existing error state", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("connection refused"));

    const result = await loadArchiveDates({
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load archive dates."
    });
  });
});
