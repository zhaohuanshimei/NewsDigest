import type { MockArchiveState } from "../content/getArchiveDates";
import type { MockDigestState } from "../content/getLatestDigest";

export const SITE_TITLE = "News Digest";
export const SITE_DESCRIPTION = "A calm daily briefing on the latest global stories.";
export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8001/api/v1";

export function readMockDigestOverride(
  value: string | undefined
): MockDigestState | undefined {
  if (value === "success" || value === "empty" || value === "error") {
    return value;
  }

  return undefined;
}

export function readMockArchiveOverride(
  value: string | undefined
): MockArchiveState | undefined {
  if (value === "success" || value === "empty" || value === "error") {
    return value;
  }

  return undefined;
}

export function readApiBaseUrl(value: string | undefined): string {
  const trimmedValue = value?.trim();

  if (!trimmedValue) {
    return DEFAULT_API_BASE_URL;
  }

  return trimmedValue.replace(/\/+$/, "");
}
