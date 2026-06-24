import type { MockDigestState } from "../content/getLatestDigest";

export const SITE_TITLE = "News Digest";
export const SITE_DESCRIPTION = "A calm daily briefing on the latest global stories.";

export function readMockDigestState(value: string | undefined): MockDigestState {
  if (value === "empty" || value === "error") {
    return value;
  }

  return "success";
}
