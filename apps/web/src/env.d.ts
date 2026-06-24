/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_DIGEST_STATE?: "success" | "empty" | "error";
  readonly NEWS_DIGEST_API_BASE_URL?: string;
}
