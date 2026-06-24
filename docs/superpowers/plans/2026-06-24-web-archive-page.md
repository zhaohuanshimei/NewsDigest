# Web Archive Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real `/archive` page in `apps/web` that fetches archive dates from the API by default, supports controlled success/empty/error states, and passes seam plus build-time rendering tests.

**Architecture:** The archive page mirrors the homepage pattern already established in `apps/web`: a page-level Astro route depends on a single content seam, and the seam hides whether data comes from the real API or a local override. UI components stay dumb and static, while the config/content layers own API URLs, env switches, and response mapping.

**Tech Stack:** `Astro`, `TypeScript`, `Vitest`, local shared contracts from `packages/shared-types`

## Global Constraints

- Use `Astro + TypeScript` for `apps/web`.
- Add an independent `/archive` route instead of expanding the homepage.
- Default to the real API `GET /api/v1/archive/dates`.
- Use a dedicated override switch `PUBLIC_ARCHIVE_STATE=success|empty|error`.
- Keep the same seam architecture already used by the homepage.
- Preserve the "极简升级版" direction: single column, large whitespace, system font stack, and zero runtime JS.
- Do not implement `/digests/[date]`, cluster/article detail pages, pagination, grouping, search, or client-side interactions in this plan.
- Build tests must use isolated output directories so parallel test execution cannot stomp shared `dist/`.

---

### Task 1: Add The Archive Content Seam

**Files:**
- Create: `apps/web/src/lib/content/mockArchive.ts`
- Create: `apps/web/src/lib/content/getArchiveDates.ts`
- Modify: `apps/web/src/lib/config/site.ts`
- Modify: `apps/web/src/env.d.ts`
- Test: `apps/web/tests/content/getArchiveDates.test.ts`

**Interfaces:**
- Consumes:
  - `ArchiveDateListResource` from `../../../../../packages/shared-types/src/index.ts`
  - `readApiBaseUrl(value: string | undefined): string`
- Produces:
  - `export type MockArchiveState = "success" | "empty" | "error"`
  - `export type ArchivePageState = { kind: "success"; dates: string[] } | { kind: "empty" } | { kind: "error"; message: string }`
  - `export interface LoadArchiveDatesOptions { stateOverride?: MockArchiveState; apiBaseUrl?: string; fetchImpl?: typeof fetch }`
  - `export function readMockArchiveOverride(value: string | undefined): MockArchiveState | undefined`
  - `export async function loadArchiveDates(options?: LoadArchiveDatesOptions): Promise<ArchivePageState>`

- [ ] **Step 1: Write the failing seam test**

Create `apps/web/tests/content/getArchiveDates.test.ts`:

```ts
import { describe, expect, it, vi } from "vitest";

import { loadArchiveDates } from "../../src/lib/content/getArchiveDates";

describe("loadArchiveDates", () => {
  it("returns a success state when the archive success override is enabled", async () => {
    const result = await loadArchiveDates({ stateOverride: "success" });

    expect(result).toEqual({
      kind: "success",
      dates: ["2026-06-24", "2026-06-23", "2026-06-22"]
    });
  });

  it("returns an empty state when the seam is told to simulate no archive dates", async () => {
    const result = await loadArchiveDates({ stateOverride: "empty" });

    expect(result).toEqual({ kind: "empty" });
  });

  it("returns an error state when the seam is told to simulate a failure", async () => {
    const result = await loadArchiveDates({ stateOverride: "error" });

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load archive dates."
    });
  });

  it("fetches archive dates from the real API when no override is present", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        dates: ["2026-06-24", "2026-06-23"]
      })
    });

    const result = await loadArchiveDates({
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(fetchImpl).toHaveBeenCalledWith(
      "http://127.0.0.1:8001/api/v1/archive/dates",
      expect.objectContaining({
        headers: {
          accept: "application/json"
        }
      })
    );
    expect(result).toEqual({
      kind: "success",
      dates: ["2026-06-24", "2026-06-23"]
    });
  });

  it("maps an empty archive list response to the empty state", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        dates: []
      })
    });

    const result = await loadArchiveDates({
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(result).toEqual({ kind: "empty" });
  });

  it("maps network failures to the existing error state", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("connection refused"));

    const result = await loadArchiveDates({
      apiBaseUrl: "http://127.0.0.1:8001/api/v1",
      fetchImpl
    });

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load archive dates."
    });
  });
});
```

- [ ] **Step 2: Run the seam test to verify it fails**

Run: `npm --prefix apps/web run test -- tests/content/getArchiveDates.test.ts`
Expected: FAIL with `Cannot find module '../../src/lib/content/getArchiveDates'` or equivalent.

- [ ] **Step 3: Add the archive mock data**

Create `apps/web/src/lib/content/mockArchive.ts`:

```ts
import type { ArchiveDateListResource } from "../../../../../packages/shared-types/src/index.ts";

export const MOCK_ARCHIVE_DATES: ArchiveDateListResource = {
  dates: ["2026-06-24", "2026-06-23", "2026-06-22"]
};
```

- [ ] **Step 4: Extend the site config with archive override support**

Update `apps/web/src/lib/config/site.ts`:

```ts
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
```

- [ ] **Step 5: Extend env typing for the archive override**

Update `apps/web/src/env.d.ts`:

```ts
/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_DIGEST_STATE?: "success" | "empty" | "error";
  readonly PUBLIC_ARCHIVE_STATE?: "success" | "empty" | "error";
  readonly NEWS_DIGEST_API_BASE_URL?: string;
}
```

- [ ] **Step 6: Implement the archive seam**

Create `apps/web/src/lib/content/getArchiveDates.ts`:

```ts
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
```

- [ ] **Step 7: Run the seam test to verify it passes**

Run: `npm --prefix apps/web run test -- tests/content/getArchiveDates.test.ts`
Expected: PASS with 6 tests passing.

- [ ] **Step 8: Commit the seam**

```bash
git add apps/web/src/lib/content/mockArchive.ts apps/web/src/lib/content/getArchiveDates.ts apps/web/src/lib/config/site.ts apps/web/src/env.d.ts apps/web/tests/content/getArchiveDates.test.ts
git commit -m "feat: add archive dates content seam"
```

### Task 2: Render The Archive Success State

**Files:**
- Create: `apps/web/src/components/archive/ArchiveHeader.astro`
- Create: `apps/web/src/components/archive/ArchiveDateList.astro`
- Create: `apps/web/src/components/archive/ArchiveDateItem.astro`
- Create: `apps/web/src/pages/archive.astro`
- Modify: `apps/web/src/styles/global.css`
- Test: `apps/web/tests/archive-page.test.ts`

**Interfaces:**
- Consumes:
  - `BaseLayout.astro` props: `{ title: string; description?: string }`
  - `SITE_TITLE`, `SITE_DESCRIPTION`
  - `loadArchiveDates(options?: LoadArchiveDatesOptions): Promise<ArchivePageState>`
- Produces:
  - `ArchiveHeader.astro` props: `{ count: number }`
  - `ArchiveDateList.astro` props: `{ dates: string[] }`
  - `ArchiveDateItem.astro` props: `{ date: string }`
  - `/archive` success render path

- [ ] **Step 1: Write the failing archive page success-build test**

Create `apps/web/tests/archive-page.test.ts`:

```ts
import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");
const outDir = "dist-archive-success";

describe("archive page success build", () => {
  it("renders archive dates when the success override is enabled", () => {
    rmSync(resolve(appDir, outDir), { force: true, recursive: true });

    execSync(`npm run build -- --outDir ${outDir}`, {
      cwd: appDir,
      env: {
        ...process.env,
        PUBLIC_ARCHIVE_STATE: "success"
      },
      stdio: "pipe"
    });

    const html = readFileSync(resolve(appDir, outDir, "archive/index.html"), "utf8");

    expect(html).toContain("Archive");
    expect(html).toContain("2026-06-24");
    expect(html).toContain("2026-06-23");
  });
});
```

- [ ] **Step 2: Run the archive page success-build test to verify it fails**

Run: `npm --prefix apps/web run test -- tests/archive-page.test.ts`
Expected: FAIL because `/archive` does not exist yet.

- [ ] **Step 3: Add the archive presentation components**

Create `apps/web/src/components/archive/ArchiveHeader.astro`:

```astro
---
interface Props {
  count: number;
}

const { count } = Astro.props;
---

<header class="archive-header">
  <p class="page-eyebrow">Archive</p>
  <h1 class="archive-title">Past digest publication dates</h1>
  <p class="archive-description">{count} published digests currently listed.</p>
</header>
```

Create `apps/web/src/components/archive/ArchiveDateItem.astro`:

```astro
---
interface Props {
  date: string;
}

const { date } = Astro.props;
---

<li class="archive-date-item">
  <span class="archive-date-label">{date}</span>
</li>
```

Create `apps/web/src/components/archive/ArchiveDateList.astro`:

```astro
---
import ArchiveDateItem from "./ArchiveDateItem.astro";

interface Props {
  dates: string[];
}

const { dates } = Astro.props;
---

<ul class="archive-date-list" aria-label="Archive dates">
  {dates.map((date) => <ArchiveDateItem date={date} />)}
</ul>
```

- [ ] **Step 4: Add the archive route**

Create `apps/web/src/pages/archive.astro`:

```astro
---
import ArchiveDateList from "../components/archive/ArchiveDateList.astro";
import ArchiveHeader from "../components/archive/ArchiveHeader.astro";
import EmptyState from "../components/states/EmptyState.astro";
import ErrorState from "../components/states/ErrorState.astro";
import BaseLayout from "../layouts/BaseLayout.astro";
import { SITE_DESCRIPTION, SITE_TITLE } from "../lib/config/site";
import { loadArchiveDates } from "../lib/content/getArchiveDates";

const archiveState = await loadArchiveDates();
---

<BaseLayout title={`${SITE_TITLE} Archive`} description={SITE_DESCRIPTION}>
  <main class="page-shell">
    {
      archiveState.kind === "success" ? (
        <section class="archive-surface" aria-label="Archive dates">
          <ArchiveHeader count={archiveState.dates.length} />
          <ArchiveDateList dates={archiveState.dates} />
        </section>
      ) : archiveState.kind === "empty" ? (
        <EmptyState />
      ) : (
        <ErrorState message={archiveState.message} />
      )
    }
  </main>
</BaseLayout>
```

- [ ] **Step 5: Add the archive styles without introducing a second visual system**

Append to `apps/web/src/styles/global.css`:

```css
.archive-surface {
  background: var(--surface-background);
  border: 1px solid var(--surface-border);
  padding: 2rem 0;
}

.archive-header {
  display: grid;
  gap: 0.8rem;
  padding: 0 1.5rem 2rem;
  border-bottom: 1px solid var(--surface-border);
}

.archive-title {
  max-width: 18ch;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1;
  letter-spacing: -0.035em;
}

.archive-description {
  max-width: 36rem;
  font-size: 0.98rem;
  line-height: 1.75;
  color: var(--muted-text);
}

.archive-date-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.archive-date-item {
  padding: 1.2rem 1.5rem;
  border-bottom: 1px solid var(--surface-border);
}

.archive-date-item:last-child {
  border-bottom: 0;
}

.archive-date-label {
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--headline-text);
}

@media (min-width: 48rem) {
  .archive-header,
  .archive-date-item {
    padding-left: 2rem;
    padding-right: 2rem;
  }
}
```

- [ ] **Step 6: Run the archive page success-build test to verify it passes**

Run: `npm --prefix apps/web run test -- tests/archive-page.test.ts`
Expected: PASS with `/archive` build output containing the archive heading and date list.

- [ ] **Step 7: Commit the archive success page**

```bash
git add apps/web/src/components/archive apps/web/src/pages/archive.astro apps/web/src/styles/global.css apps/web/tests/archive-page.test.ts
git commit -m "feat: render archive page success state"
```

### Task 3: Add Archive Empty/Error Verification And Docs

**Files:**
- Create: `apps/web/tests/archive-page-states.test.ts`
- Modify: `apps/web/README.md`

**Interfaces:**
- Consumes:
  - `PUBLIC_ARCHIVE_STATE`
  - `/archive` route implemented in Task 2
- Produces:
  - Alternate-state build coverage for `/archive`
  - Updated local run documentation

- [ ] **Step 1: Write the failing archive alternate-state build test**

Create `apps/web/tests/archive-page-states.test.ts`:

```ts
import { execSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");

function buildArchiveAndRead(state: "empty" | "error"): string {
  const outDir = `dist-archive-${state}`;

  rmSync(resolve(appDir, outDir), { force: true, recursive: true });

  execSync(`npm run build -- --outDir ${outDir}`, {
    cwd: appDir,
    env: {
      ...process.env,
      PUBLIC_ARCHIVE_STATE: state
    },
    stdio: "pipe"
  });

  return readFileSync(resolve(appDir, outDir, "archive/index.html"), "utf8");
}

describe("archive page alternate states", () => {
  it("renders an empty-state message", () => {
    const html = buildArchiveAndRead("empty");

    expect(html).toContain("No digest published yet.");
  });

  it("renders an error-state message", () => {
    const html = buildArchiveAndRead("error");

    expect(html).toContain("Unable to load archive dates.");
  });
});
```

- [ ] **Step 2: Run the archive alternate-state build test to verify it fails**

Run: `npm --prefix apps/web run test -- tests/archive-page-states.test.ts`
Expected: FAIL because the route has not yet been validated for alternate states.

- [ ] **Step 3: Update the web README with archive run instructions**

Update `apps/web/README.md`:

```md
# apps/web

News Digest V2 web client built with Astro.

## Commands

```bash
npm install
npm run dev
npm run build
npm run check
```

## API Integration

Homepage data now fetches from `GET /api/v1/digests/latest` at build time or on the Astro server.

```bash
NEWS_DIGEST_API_BASE_URL=http://127.0.0.1:8001/api/v1 npm run dev
NEWS_DIGEST_API_BASE_URL=http://127.0.0.1:8001/api/v1 npm run build
```

## Mock State Switches

Use state overrides to temporarily bypass the real API during local verification:

```bash
PUBLIC_DIGEST_STATE=success npm run dev
PUBLIC_DIGEST_STATE=empty npm run build
PUBLIC_DIGEST_STATE=error npm run build

PUBLIC_ARCHIVE_STATE=success npm run build
PUBLIC_ARCHIVE_STATE=empty npm run build
PUBLIC_ARCHIVE_STATE=error npm run build
```
```

- [ ] **Step 4: Run the archive alternate-state build test to verify it passes**

Run: `npm --prefix apps/web run test -- tests/archive-page-states.test.ts`
Expected: PASS with both archive alternate-state cases green.

- [ ] **Step 5: Run the full web verification suite**

Run: `npm --prefix apps/web run test`
Expected: PASS with homepage seam tests, homepage build tests, archive seam tests, and archive build tests all green.

Run: `npm --prefix apps/web run check`
Expected: PASS with `astro check` and `vitest run` both green.

- [ ] **Step 6: Commit the archive verification and docs**

```bash
git add apps/web/tests/archive-page-states.test.ts apps/web/README.md
git commit -m "feat: add archive page states"
```

## Plan Self-Review

- Spec coverage:
  - Independent `/archive` route is covered in Task 2.
  - Real API seam to `GET /api/v1/archive/dates` is covered in Task 1.
  - Dedicated `PUBLIC_ARCHIVE_STATE` override is covered in Task 1 and Task 3.
  - Minimal list-only UI and reuse of the visual system are covered in Task 2.
  - Success/empty/error verification and isolated build outputs are covered in Tasks 2 and 3.
- Placeholder scan:
  - No `TODO`, `TBD`, "similar to", or hidden follow-up instructions remain.
- Type consistency:
  - `MockArchiveState`, `ArchivePageState`, `LoadArchiveDatesOptions`, `readMockArchiveOverride()`, and `loadArchiveDates()` are defined once in Task 1 and reused consistently in later tasks.

Plan complete and saved to `docs/superpowers/plans/2026-06-24-web-archive-page.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
