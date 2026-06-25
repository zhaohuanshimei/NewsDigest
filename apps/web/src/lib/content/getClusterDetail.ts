import type { ClusterDetailResource } from "../../../../../packages/shared-types/src/index.ts";

import { readApiBaseUrl, readMockClusterOverride } from "../config/site";
import { MOCK_CLUSTER_DETAIL } from "./mockCluster";

export type MockClusterState = "success" | "not-found" | "error";

export type ClusterPageState =
  | { kind: "success"; cluster: ClusterDetailResource }
  | { kind: "not-found" }
  | { kind: "error"; message: string };

export interface LoadClusterDetailOptions {
  stateOverride?: MockClusterState;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

function isClusterDetailResource(value: unknown): value is ClusterDetailResource {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<ClusterDetailResource>;

  return (
    typeof candidate.id === "string" &&
    typeof candidate.category === "string" &&
    typeof candidate.headline === "string" &&
    typeof candidate.summary === "string" &&
    typeof candidate.source_count === "number" &&
    Array.isArray(candidate.digest_dates) &&
    candidate.digest_dates.every((date) => typeof date === "string")
  );
}

export async function loadClusterDetail(
  clusterId: string,
  options: LoadClusterDetailOptions = {}
): Promise<ClusterPageState> {
  const stateOverride =
    options.stateOverride ??
    readMockClusterOverride(import.meta.env.PUBLIC_CLUSTER_STATE);

  if (stateOverride === "success") {
    return {
      kind: "success",
      cluster: structuredClone(MOCK_CLUSTER_DETAIL)
    };
  }

  if (stateOverride === "not-found") {
    return { kind: "not-found" };
  }

  if (stateOverride === "error") {
    return {
      kind: "error",
      message: "Unable to load this cluster."
    };
  }

  const apiBaseUrl =
    options.apiBaseUrl ?? readApiBaseUrl(import.meta.env.NEWS_DIGEST_API_BASE_URL);
  const fetchImpl = options.fetchImpl ?? fetch;

  try {
    const response = await fetchImpl(`${apiBaseUrl}/clusters/${clusterId}`, {
      headers: {
        accept: "application/json"
      }
    });

    if (response.status === 404) {
      return { kind: "not-found" };
    }

    if (!response.ok) {
      return {
        kind: "error",
        message: `Cluster request failed with status ${response.status}.`
      };
    }

    const payload = (await response.json()) as unknown;
    if (!isClusterDetailResource(payload)) {
      return {
        kind: "error",
        message: "Cluster response did not match the expected contract."
      };
    }

    return {
      kind: "success",
      cluster: payload
    };
  } catch {
    return {
      kind: "error",
      message: "Unable to load this cluster."
    };
  }
}
