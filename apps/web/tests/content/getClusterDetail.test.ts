import { describe, expect, it, vi } from "vitest";

import { loadClusterDetail } from "../../src/lib/content/getClusterDetail";

const MOCK_CLUSTER = {
  id: "cluster-ai-chip-001",
  category: "technology",
  headline: "AI 芯片与模型基础设施继续升温",
  summary: "多家厂商围绕训练基础设施与推理部署发布新进展，覆盖训练算力、推理成本与生态合作。",
  source_count: 3,
  digest_dates: ["2026-06-24"]
};

describe("loadClusterDetail", () => {
  it("returns a success state when the cluster success override is enabled", async () => {
    const result = await loadClusterDetail("cluster-ai-chip-001", {
      stateOverride: "success"
    });

    expect(result).toEqual({
      kind: "success",
      cluster: MOCK_CLUSTER
    });
  });

  it("returns a not-found state when the seam is told to simulate a missing cluster", async () => {
    const result = await loadClusterDetail("cluster-missing", {
      stateOverride: "not-found"
    });

    expect(result).toEqual({ kind: "not-found" });
  });

  it("returns an error state when the seam is told to simulate a failure", async () => {
    const result = await loadClusterDetail("cluster-ai-chip-001", {
      stateOverride: "error"
    });

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load this cluster."
    });
  });

  it("fetches the cluster from the real API when no override is present", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => MOCK_CLUSTER
    });

    const result = await loadClusterDetail("cluster-ai-chip-001", {
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(fetchImpl).toHaveBeenCalledWith(
      "http://127.0.0.1:8001/api/v1/clusters/cluster-ai-chip-001",
      expect.objectContaining({
        headers: {
          accept: "application/json"
        }
      })
    );
    expect(result).toEqual({
      kind: "success",
      cluster: MOCK_CLUSTER
    });
  });

  it("maps a 404 response to the not-found state", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ error: { code: "not_found" } })
    });

    const result = await loadClusterDetail("cluster-missing", {
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(result).toEqual({ kind: "not-found" });
  });

  it("maps a contract mismatch to the error state", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: "cluster-ai-chip-001" })
    });

    const result = await loadClusterDetail("cluster-ai-chip-001", {
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(result).toEqual({
      kind: "error",
      message: "Cluster response did not match the expected contract."
    });
  });

  it("maps network failures to the error state", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("connection refused"));

    const result = await loadClusterDetail("cluster-ai-chip-001", {
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load this cluster."
    });
  });
});
