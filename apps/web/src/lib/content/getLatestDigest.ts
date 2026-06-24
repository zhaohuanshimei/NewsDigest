import type { DigestResource } from "../../../../../packages/shared-types/src/index.ts";

import { readApiBaseUrl, readMockDigestOverride } from "../config/site";
import { MOCK_LATEST_DIGEST } from "./mockDigest";

export type MockDigestState = "success" | "empty" | "error";

export type HomepageDigestState =
  | { kind: "success"; digest: DigestResource }
  | { kind: "empty" }
  | { kind: "error"; message: string };

export interface LoadHomepageDigestOptions {
  stateOverride?: MockDigestState;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

function isDigestResource(value: unknown): value is DigestResource {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<DigestResource>;

  return (
    typeof candidate.date === "string" &&
    typeof candidate.published_at === "string" &&
    Array.isArray(candidate.entries)
  );
}

export async function loadHomepageDigest(
  options: LoadHomepageDigestOptions = {}
): Promise<HomepageDigestState> {
  const stateOverride =
    options.stateOverride ??
    readMockDigestOverride(import.meta.env.PUBLIC_DIGEST_STATE);

  if (stateOverride === "success") {
    return {
      kind: "success",
      digest: structuredClone(MOCK_LATEST_DIGEST)
    };
  }

  if (stateOverride === "empty") {
    return { kind: "empty" };
  }

  if (stateOverride === "error") {
    return {
      kind: "error",
      message: "Unable to load latest digest."
    };
  }

  const apiBaseUrl =
    options.apiBaseUrl ?? readApiBaseUrl(import.meta.env.NEWS_DIGEST_API_BASE_URL);
  const fetchImpl = options.fetchImpl ?? fetch;

  try {
    const response = await fetchImpl(`${apiBaseUrl}/digests/latest`, {
      headers: {
        accept: "application/json"
      }
    });

    if (response.status === 404) {
      return { kind: "empty" };
    }

    if (!response.ok) {
      return {
        kind: "error",
        message: `Latest digest request failed with status ${response.status}.`
      };
    }

    const payload = (await response.json()) as unknown;
    if (!isDigestResource(payload)) {
      return {
        kind: "error",
        message: "Latest digest response did not match the expected contract."
      };
    }

    return {
      kind: "success",
      digest: payload
    };
  } catch {
    return {
      kind: "error",
      message: "Unable to load latest digest."
    };
  }
}
