# Web Cluster Detail Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first detail page in `apps/web`: a dynamic `/clusters/[id]` route that fetches a single cluster from the API by default, supports controlled success/not-found/error states, links the homepage digest entry to its real cluster detail, and passes seam plus build-time rendering tests.

**Architecture:** The cluster detail page mirrors the homepage and archive patterns already established in `apps/web`: a page-level Astro route depends on a single content seam, and the seam hides whether data comes from the real API or a local override. The only new structural concern is that `/clusters/[id]` is a *dynamic* route, so static builds require `getStaticPaths()`. This plan keeps that list fixed to a single known cluster id for now and defers real id discovery to a later round.

**Tech Stack:** `Astro`, `TypeScript`, `Vitest`, local shared contracts from `packages/shared-types`

## Global Constraints

- Use `Astro + TypeScript` for `apps/web`.
- Add a dynamic `/clusters/[id]` route; do not add `/articles/[id]` or `/digests/[date]` in this plan.
- Default to the real API `GET /api/v1/clusters/{cluster_id}`.
- Map `200` to `success`, `404` to `not-found`, and any other failure (non-ok status, contract mismatch, network error) to `error`.
- Keep `not-found` distinct from `error`; never collapse a `404` into the generic error panel.
- Use a dedicated override switch `PUBLIC_CLUSTER_STATE=success|not-found|error`, independent from `PUBLIC_DIGEST_STATE` and `PUBLIC_ARCHIVE_STATE`.
- Keep the same seam architecture already used by the homepage and archive page.
- Only render fields the current `ClusterDetailResource` contract guarantees. Do not fabricate related-article lists, source names, or external links.
- The homepage digest entry must link to its real cluster detail at `/clusters/{cluster_id}`.
- `getStaticPaths()` returns a fixed known id list this round (`cluster-ai-chip-001`); real id discovery from the API is out of scope.
- Preserve the "极简升级版" direction: single column, large whitespace, system font stack, and zero runtime JS.
- Build tests must use isolated output directories so parallel test execution cannot stomp shared `dist/`.
- Build tests must set an explicit timeout consistent with the existing homepage/archive build tests.

---

### Task 1: Add The Cluster Content Seam

**Files:**
- Create: `apps/web/src/lib/content/mockCluster.ts`
- Create: `apps/web/src/lib/content/getClusterDetail.ts`
- Modify: `apps/web/src/lib/config/site.ts`
- Modify: `apps/web/src/env.d.ts`
- Test: `apps/web/tests/content/getClusterDetail.test.ts`

**Interfaces:**
- Consumes:
  - `ClusterDetailResource` from `../../../../../packages/shared-types/src/index.ts`
  - `readApiBaseUrl(value: string | undefined): string`
- Produces:
  - `export type MockClusterState = "success" | "not-found" | "error"`
  - `export type ClusterPageState = { kind: "success"; cluster: ClusterDetailResource } | { kind: "not-found" } | { kind: "error"; message: string }`
  - `export interface LoadClusterDetailOptions { stateOverride?: MockClusterState; apiBaseUrl?: string; fetchImpl?: typeof fetch }`
  - `export function readMockClusterOverride(value: string | undefined): MockClusterState | undefined`
  - `export async function loadClusterDetail(clusterId: string, options?: LoadClusterDetailOptions): Promise<ClusterPageState>`

- [ ] **Step 1: Write the failing seam test**

Create `apps/web/tests/content/getClusterDetail.test.ts`:

```ts
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
```

- [ ] **Step 2: Run the seam test to verify it fails**

Run: `npm --prefix apps/web run test -- tests/content/getClusterDetail.test.ts`
Expected: FAIL with `Cannot find module '../../src/lib/content/getClusterDetail'` or equivalent.

- [ ] **Step 3: Add the cluster mock data**

Create `apps/web/src/lib/content/mockCluster.ts`:

```ts
import type { ClusterDetailResource } from "../../../../../packages/shared-types/src/index.ts";

export const MOCK_CLUSTER_DETAIL: ClusterDetailResource = {
  id: "cluster-ai-chip-001",
  category: "technology",
  headline: "AI 芯片与模型基础设施继续升温",
  summary: "多家厂商围绕训练基础设施与推理部署发布新进展，覆盖训练算力、推理成本与生态合作。",
  source_count: 3,
  digest_dates: ["2026-06-24"]
};
```

- [ ] **Step 4: Extend the site config with cluster override support**

Add the cluster override reader to `apps/web/src/lib/config/site.ts`. Keep the existing exports unchanged and add the new type import plus reader:

```ts
import type { MockArchiveState } from "../content/getArchiveDates";
import type { MockClusterState } from "../content/getClusterDetail";
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

export function readMockClusterOverride(
  value: string | undefined
): MockClusterState | undefined {
  if (value === "success" || value === "not-found" || value === "error") {
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
```

- [ ] **Step 5: Extend env typing for the cluster override**

Update `apps/web/src/env.d.ts`:

```ts
/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_DIGEST_STATE?: "success" | "empty" | "error";
  readonly PUBLIC_ARCHIVE_STATE?: "success" | "empty" | "error";
  readonly PUBLIC_CLUSTER_STATE?: "success" | "not-found" | "error";
  readonly NEWS_DIGEST_API_BASE_URL?: string;
}
```

- [ ] **Step 6: Implement the cluster seam**

Create `apps/web/src/lib/content/getClusterDetail.ts`:

```ts
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
```

- [ ] **Step 7: Run the seam test to verify it passes**

Run: `npm --prefix apps/web run test -- tests/content/getClusterDetail.test.ts`
Expected: PASS with 7 tests passing.

- [ ] **Step 8: Commit the seam**

```bash
git add apps/web/src/lib/content/mockCluster.ts apps/web/src/lib/content/getClusterDetail.ts apps/web/src/lib/config/site.ts apps/web/src/env.d.ts apps/web/tests/content/getClusterDetail.test.ts
git commit -m "feat: add cluster detail content seam"
```

### Task 2: Render The Cluster Detail Success State And Link The Homepage

**Files:**
- Create: `apps/web/src/components/cluster/ClusterDetailHeader.astro`
- Create: `apps/web/src/components/cluster/ClusterMetaList.astro`
- Create: `apps/web/src/pages/clusters/[id].astro`
- Modify: `apps/web/src/components/digest/DigestEntryItem.astro`
- Modify: `apps/web/src/styles/global.css`
- Test: `apps/web/tests/cluster-page.test.ts`
- Test: `apps/web/tests/homepage-cluster-link.test.ts`

**Interfaces:**
- Consumes:
  - `BaseLayout.astro` props: `{ title: string; description?: string }`
  - `SITE_TITLE`, `SITE_DESCRIPTION`
  - `loadClusterDetail(clusterId: string, options?: LoadClusterDetailOptions): Promise<ClusterPageState>`
- Produces:
  - `ClusterDetailHeader.astro` props: `{ category: string; headline: string; summary: string }`
  - `ClusterMetaList.astro` props: `{ sourceCount: number; digestDates: string[] }`
  - `/clusters/[id]` success render path
  - Homepage digest entry headline linked to `/clusters/{cluster_id}`

- [ ] **Step 1: Write the failing cluster page success-build test**

Create `apps/web/tests/cluster-page.test.ts`:

```ts
import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");
const outDir = "dist-cluster-success";

describe("cluster detail page success build", () => {
  it("renders cluster detail when the success override is enabled", () => {
    rmSync(resolve(appDir, outDir), { force: true, recursive: true });

    execSync(`npm run build -- --outDir ${outDir}`, {
      cwd: appDir,
      env: {
        ...process.env,
        PUBLIC_CLUSTER_STATE: "success"
      },
      stdio: "pipe"
    });

    const html = readFileSync(
      resolve(appDir, outDir, "clusters/cluster-ai-chip-001/index.html"),
      "utf8"
    );

    expect(html).toContain("technology");
    expect(html).toContain("AI 芯片与模型基础设施继续升温");
    expect(html).toContain("3 sources");
    expect(html).toContain("2026-06-24");
  }, 60000);
});
```

- [ ] **Step 2: Run the cluster page success-build test to verify it fails**

Run: `npm --prefix apps/web run test -- tests/cluster-page.test.ts`
Expected: FAIL because `/clusters/[id]` does not exist yet.

- [ ] **Step 3: Add the cluster presentation components**

Create `apps/web/src/components/cluster/ClusterDetailHeader.astro`:

```astro
---
interface Props {
  category: string;
  headline: string;
  summary: string;
}

const { category, headline, summary } = Astro.props;
---

<header class="cluster-header">
  <p class="page-eyebrow">{category}</p>
  <h1 class="cluster-title">{headline}</h1>
  <p class="cluster-summary">{summary}</p>
</header>
```

Create `apps/web/src/components/cluster/ClusterMetaList.astro`:

```astro
---
interface Props {
  sourceCount: number;
  digestDates: string[];
}

const { sourceCount, digestDates } = Astro.props;
---

<dl class="cluster-meta" aria-label="Cluster metadata">
  <div class="cluster-meta-row">
    <dt class="cluster-meta-term">Sources</dt>
    <dd class="cluster-meta-value">{sourceCount} sources</dd>
  </div>
  <div class="cluster-meta-row">
    <dt class="cluster-meta-term">Digest dates</dt>
    <dd class="cluster-meta-value">
      <ul class="cluster-date-list">
        {digestDates.map((date) => <li class="cluster-date-item">{date}</li>)}
      </ul>
    </dd>
  </div>
</dl>
```

- [ ] **Step 4: Add the dynamic cluster route**

Create `apps/web/src/pages/clusters/[id].astro`. The `getStaticPaths()` list is fixed to the single known cluster id this round; expanding it to real API ids is out of scope.

```astro
---
import type { GetStaticPaths } from "astro";

import ClusterDetailHeader from "../../components/cluster/ClusterDetailHeader.astro";
import ClusterMetaList from "../../components/cluster/ClusterMetaList.astro";
import ErrorState from "../../components/states/ErrorState.astro";
import BaseLayout from "../../layouts/BaseLayout.astro";
import { SITE_DESCRIPTION, SITE_TITLE } from "../../lib/config/site";
import { loadClusterDetail } from "../../lib/content/getClusterDetail";

export const getStaticPaths = (() => {
  return [{ params: { id: "cluster-ai-chip-001" } }];
}) satisfies GetStaticPaths;

const clusterId = Astro.params.id ?? "";
const clusterState = await loadClusterDetail(clusterId);
---

<BaseLayout title={`${SITE_TITLE} Cluster`} description={SITE_DESCRIPTION}>
  <main class="page-shell">
    {
      clusterState.kind === "success" ? (
        <section class="cluster-surface" aria-label="Cluster detail">
          <ClusterDetailHeader
            category={clusterState.cluster.category}
            headline={clusterState.cluster.headline}
            summary={clusterState.cluster.summary}
          />
          <ClusterMetaList
            sourceCount={clusterState.cluster.source_count}
            digestDates={clusterState.cluster.digest_dates}
          />
        </section>
      ) : clusterState.kind === "not-found" ? (
        <section class="state-panel" aria-live="polite">
          <h2 class="state-title">This cluster is not available.</h2>
          <p class="state-copy">
            The requested cluster does not exist or is no longer available.
          </p>
        </section>
      ) : (
        <ErrorState message={clusterState.message} />
      )
    }
  </main>
</BaseLayout>
```

- [ ] **Step 5: Link the homepage digest entry to its cluster detail**

Update `apps/web/src/components/digest/DigestEntryItem.astro` so the headline links to the real cluster detail route:

```astro
---
import type { DigestEntryResource } from "../../../../../packages/shared-types/src/index.ts";

interface Props {
  entry: DigestEntryResource;
}

const { entry } = Astro.props;
---

<article class="digest-entry">
  <p class="digest-entry-rank">{entry.rank.toString().padStart(2, "0")}</p>
  <h3 class="digest-entry-headline">
    <a class="digest-entry-link" href={`/clusters/${entry.cluster_id}`}>{entry.headline}</a>
  </h3>
  <p class="digest-entry-summary">{entry.summary}</p>
  <p class="digest-entry-meta">{entry.source_count} sources</p>
</article>
```

- [ ] **Step 6: Add the cluster styles without introducing a second visual system**

Append to `apps/web/src/styles/global.css`:

```css
.cluster-surface {
  background: var(--surface-background);
  border: 1px solid var(--surface-border);
  padding: 2rem 0;
}

.cluster-header {
  display: grid;
  gap: 0.9rem;
  padding: 0 1.5rem 2rem;
  border-bottom: 1px solid var(--surface-border);
}

.cluster-title {
  max-width: 22ch;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.05;
  letter-spacing: -0.035em;
}

.cluster-summary {
  max-width: 42rem;
  font-size: 1.05rem;
  line-height: 1.75;
  color: var(--muted-text);
}

.cluster-meta {
  display: grid;
  gap: 1.2rem;
  margin: 0;
  padding: 1.6rem 1.5rem 0;
}

.cluster-meta-row {
  display: grid;
  gap: 0.4rem;
}

.cluster-meta-term {
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted-text);
}

.cluster-meta-value {
  margin: 0;
  font-size: 1.02rem;
  line-height: 1.6;
  color: var(--headline-text);
}

.cluster-date-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.cluster-date-item {
  border: 1px solid var(--surface-border);
  padding: 0.3rem 0.7rem;
  font-size: 0.95rem;
}

.digest-entry-link {
  color: inherit;
  text-decoration: none;
}

.digest-entry-link:hover,
.digest-entry-link:focus-visible {
  text-decoration: underline;
}

@media (min-width: 48rem) {
  .cluster-header,
  .cluster-meta {
    padding-left: 2rem;
    padding-right: 2rem;
  }
}
```

- [ ] **Step 7: Write the failing homepage cluster-link build test**

Create `apps/web/tests/homepage-cluster-link.test.ts`:

```ts
import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");
const outDir = "dist-home-cluster-link";

describe("homepage cluster link build", () => {
  it("links the latest digest entry to its cluster detail page", () => {
    rmSync(resolve(appDir, outDir), { force: true, recursive: true });

    execSync(`npm run build -- --outDir ${outDir}`, {
      cwd: appDir,
      env: {
        ...process.env,
        PUBLIC_DIGEST_STATE: "success"
      },
      stdio: "pipe"
    });

    const html = readFileSync(resolve(appDir, outDir, "index.html"), "utf8");

    expect(html).toContain('href="/clusters/cluster-ai-chip-001"');
  }, 60000);
});
```

- [ ] **Step 8: Run the cluster page and homepage-link build tests to verify they pass**

Run: `npm --prefix apps/web run test -- tests/cluster-page.test.ts tests/homepage-cluster-link.test.ts`
Expected: PASS with the cluster success build rendering detail fields and the homepage build containing the cluster link.

- [ ] **Step 9: Commit the cluster success page and homepage link**

```bash
git add apps/web/src/components/cluster apps/web/src/pages/clusters apps/web/src/components/digest/DigestEntryItem.astro apps/web/src/styles/global.css apps/web/tests/cluster-page.test.ts apps/web/tests/homepage-cluster-link.test.ts
git commit -m "feat: render cluster detail success state and link homepage"
```

### Task 3: Add Cluster Not-Found/Error Verification And Docs

**Files:**
- Create: `apps/web/tests/cluster-page-states.test.ts`
- Modify: `apps/web/README.md`

**Interfaces:**
- Consumes:
  - `PUBLIC_CLUSTER_STATE`
  - `/clusters/[id]` route implemented in Task 2
- Produces:
  - Alternate-state build coverage for `/clusters/[id]`
  - Updated local run documentation

- [ ] **Step 1: Write the failing cluster alternate-state build test**

Create `apps/web/tests/cluster-page-states.test.ts`:

```ts
import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");

function buildClusterAndRead(state: "not-found" | "error"): string {
  const outDir = `dist-cluster-${state}`;

  rmSync(resolve(appDir, outDir), { force: true, recursive: true });

  execSync(`npm run build -- --outDir ${outDir}`, {
    cwd: appDir,
    env: {
      ...process.env,
      PUBLIC_CLUSTER_STATE: state
    },
    stdio: "pipe"
  });

  return readFileSync(
    resolve(appDir, outDir, "clusters/cluster-ai-chip-001/index.html"),
    "utf8"
  );
}

describe("cluster detail page alternate states", () => {
  it("renders a not-found message", () => {
    const html = buildClusterAndRead("not-found");

    expect(html).toContain("This cluster is not available.");
  }, 60000);

  it("renders an error-state message", () => {
    const html = buildClusterAndRead("error");

    expect(html).toContain("Unable to load this cluster.");
  }, 60000);
});
```

- [ ] **Step 2: Run the cluster alternate-state build test to verify it fails**

Run: `npm --prefix apps/web run test -- tests/cluster-page-states.test.ts`
Expected: FAIL because the route has not yet been validated for alternate states.

- [ ] **Step 3: Update the web README with cluster run instructions**

Add the cluster override switches to the "Mock State Switches" section of `apps/web/README.md`, alongside the existing digest and archive switches:

```md
PUBLIC_CLUSTER_STATE=success npm run build
PUBLIC_CLUSTER_STATE=not-found npm run build
PUBLIC_CLUSTER_STATE=error npm run build
```

- [ ] **Step 4: Run the cluster alternate-state build test to verify it passes**

Run: `npm --prefix apps/web run test -- tests/cluster-page-states.test.ts`
Expected: PASS with both cluster alternate-state cases green.

- [ ] **Step 5: Run the full web verification suite**

Run: `npm --prefix apps/web run test`
Expected: PASS with homepage seam/build tests, archive seam/build tests, cluster seam/build tests, homepage cluster-link test, and cluster alternate-state tests all green.

Run: `npm --prefix apps/web run check`
Expected: PASS with `astro check` and `vitest run` both green.

- [ ] **Step 6: Commit the cluster verification and docs**

```bash
git add apps/web/tests/cluster-page-states.test.ts apps/web/README.md
git commit -m "feat: add cluster detail page states"
```

## Plan Self-Review

- Spec coverage:
  - Dynamic `/clusters/[id]` route is covered in Task 2.
  - Real API seam to `GET /api/v1/clusters/{cluster_id}` is covered in Task 1.
  - Dedicated `PUBLIC_CLUSTER_STATE` override is covered in Task 1 and Task 3.
  - `success` / `not-found` / `error` three-state model, with `404` kept distinct from generic `error`, is covered in Tasks 1, 2, and 3.
  - Contract-only rendering (no fabricated related articles or external links) is covered in Task 2's components.
  - Homepage digest entry linking to `/clusters/cluster-ai-chip-001` is covered in Task 2.
  - Reuse of the existing visual system is covered in Task 2's styles.
  - Isolated build outputs and explicit build-test timeouts are covered in Tasks 2 and 3.
- Dynamic-route concern:
  - `getStaticPaths()` is explicitly fixed to a single known id this round; real id discovery is documented as out of scope, matching the spec's non-goals.
- Placeholder scan:
  - No `TODO`, `TBD`, "similar to", or hidden follow-up instructions remain.
- Type consistency:
  - `MockClusterState`, `ClusterPageState`, `LoadClusterDetailOptions`, `readMockClusterOverride()`, and `loadClusterDetail()` are defined once in Task 1 and reused consistently in later tasks.
