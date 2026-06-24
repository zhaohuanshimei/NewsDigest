import type { ArchiveDateListResource } from "../../../../../packages/shared-types/src/index.ts";

import { readApiBaseUrl, readMockArchiveOverride } from "../config/site";
import { MOCK_ARCHIVE_DATES } from "./mockArchive";

export type MockArchiveState = "success" | "empty" | "error";

export type ArchivePageState =
  | { kind: "success"; dates: string[] }
  | { kind: "empty" }
  | { kind: "error"; message: string };

export interface LoadArchiveDatesOptions {
  stateOverride?: MockArchiveState;
  apiBaseUrl?: string;
  fetchImpl?: typeof fetch;
}

function isArchiveDateListResource(value: unknown): value is ArchiveDateListResource {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<ArchiveDateListResource>;
  return Array.isArray(candidate.dates) && candidate.dates.every((date) => typeof date === "string");
}

export async function loadArchiveDates(
  options: LoadArchiveDatesOptions = {}
): Promise<ArchivePageState> {
  const stateOverride =
    options.stateOverride ??
    readMockArchiveOverride(import.meta.env.PUBLIC_ARCHIVE_STATE);

  if (stateOverride === "success") {
    return {
      kind: "success",
      dates: structuredClone(MOCK_ARCHIVE_DATES.dates)
    };
  }

  if (stateOverride === "empty") {
    return { kind: "empty" };
  }

  if (stateOverride === "error") {
    return {
      kind: "error",
      message: "Unable to load archive dates."
    };
  }

  const apiBaseUrl =
    options.apiBaseUrl ?? readApiBaseUrl(import.meta.env.NEWS_DIGEST_API_BASE_URL);
  const fetchImpl = options.fetchImpl ?? fetch;

  try {
    const response = await fetchImpl(`${apiBaseUrl}/archive/dates`, {
      headers: {
        accept: "application/json"
      }
    });

    if (!response.ok) {
      return {
        kind: "error",
        message: `Archive dates request failed with status ${response.status}.`
      };
    }

    const payload = (await response.json()) as unknown;
    if (!isArchiveDateListResource(payload)) {
      return {
        kind: "error",
        message: "Archive dates response did not match the expected contract."
      };
    }

    if (payload.dates.length === 0) {
      return { kind: "empty" };
    }

    return {
      kind: "success",
      dates: payload.dates
    };
  } catch {
    return {
      kind: "error",
      message: "Unable to load archive dates."
    };
  }
}
