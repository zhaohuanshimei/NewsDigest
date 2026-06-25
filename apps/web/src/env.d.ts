/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_DIGEST_STATE?: "success" | "empty" | "error";
  readonly PUBLIC_ARCHIVE_STATE?: "success" | "empty" | "error";
  readonly PUBLIC_CLUSTER_STATE?: "success" | "not-found" | "error";
  readonly NEWS_DIGEST_API_BASE_URL?: string;
}
