import type { DigestResource } from "../../../../../packages/shared-types/src/index.ts";

import { MOCK_LATEST_DIGEST } from "./mockDigest";

export type MockDigestState = "success" | "empty" | "error";

export type HomepageDigestState =
  | { kind: "success"; digest: DigestResource }
  | { kind: "empty" }
  | { kind: "error"; message: string };

export async function loadHomepageDigest(
  state: MockDigestState = "success"
): Promise<HomepageDigestState> {
  if (state === "empty") {
    return { kind: "empty" };
  }

  if (state === "error") {
    return {
      kind: "error",
      message: "Unable to load latest digest."
    };
  }

  return {
    kind: "success",
    digest: structuredClone(MOCK_LATEST_DIGEST)
  };
}
