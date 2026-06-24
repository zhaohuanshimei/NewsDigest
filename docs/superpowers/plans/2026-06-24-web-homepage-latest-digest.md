# Web Homepage Latest Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `apps/web` as a runnable Astro app that renders the latest digest homepage from a contract-aligned mock seam, with a first-pass minimal visual system and readable success/empty/error states.

**Architecture:** `apps/web` is an Astro + TypeScript frontend with one public route (`/`). The page consumes a single content seam, `loadHomepageDigest()`, which returns a homepage state derived from a `DigestResource`-shaped mock. UI components stay dumb and static, while the seam and state reader isolate the later switch to the real API.

**Tech Stack:** `Astro`, `TypeScript`, `Vitest`, local file dependency on `@news-digest/shared-types`

## Global Constraints

- Use `Astro + TypeScript` for `apps/web`.
- Homepage consumes a mock that reuses the real `DigestResource` contract shape.
- Homepage scope is only latest digest reading at `/`.
- Preserve the "极简升级版" direction: single column, large whitespace, system font stack, and zero runtime JS.
- Do not implement real API integration in this plan.
- Do not implement archive/date/detail/RSS pages, hydration interactions, or `packages/ui` extraction in this plan.
- Do not fabricate original article links or source names; the current `DigestEntryResource` only guarantees `headline`, `summary`, and `source_count`.

---

### Task 1: Bootstrap The Astro App Shell

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/astro.config.mjs`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/src/env.d.ts`
- Create: `apps/web/src/layouts/BaseLayout.astro`
- Create: `apps/web/src/styles/global.css`
- Create: `apps/web/src/pages/index.astro`
- Modify: `apps/web/README.md`

**Interfaces:**
- Consumes: none
- Produces:
  - `BaseLayout.astro` props: `{ title: string; description?: string }`
  - npm scripts: `dev`, `build`, `preview`, `test`, `check`

- [ ] **Step 1: Run the current build command to confirm the app does not exist yet**

Run: `npm --prefix apps/web run build`
Expected: FAIL with "Missing script: build" or equivalent because `apps/web` is still only a placeholder directory.

- [ ] **Step 2: Create the Astro package and toolchain files**

Create `apps/web/package.json`:

```json
{
  "name": "@news-digest/web",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "test": "vitest run",
    "check": "astro check && vitest run"
  },
  "dependencies": {
    "@news-digest/shared-types": "file:../../packages/shared-types",
    "astro": "^5.0.0"
  },
  "devDependencies": {
    "@types/node": "^24.0.0",
    "typescript": "^5.9.0",
    "vitest": "^3.2.0"
  }
}
```

Create `apps/web/astro.config.mjs`:

```js
import { defineConfig } from "astro/config";

export default defineConfig({
  server: {
    host: true,
    port: 4321
  }
});
```

Create `apps/web/tsconfig.json`:

```json
{
  "extends": "astro/tsconfigs/strict",
  "compilerOptions": {
    "baseUrl": "."
  }
}
```

Create `apps/web/src/env.d.ts`:

```ts
/// <reference types="astro/client" />
```

- [ ] **Step 3: Create the base layout, global styles, and placeholder homepage**

Create `apps/web/src/layouts/BaseLayout.astro`:

```astro
---
import "../styles/global.css";

interface Props {
  title: string;
  description?: string;
}

const { title, description = "Daily international digest." } = Astro.props;
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content={description} />
    <title>{title}</title>
  </head>
  <body>
    <slot />
  </body>
</html>
```

Create `apps/web/src/styles/global.css`:

```css
:root {
  color-scheme: light;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f8f6f1;
  color: #1f2328;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  background: #f8f6f1;
  color: #1f2328;
}

a {
  color: inherit;
}
```

Create `apps/web/src/pages/index.astro`:

```astro
---
import BaseLayout from "../layouts/BaseLayout.astro";
---

<BaseLayout title="News Digest">
  <main style="padding: 4rem 1.5rem;">
    <h1>News Digest</h1>
    <p>Homepage scaffold ready for latest digest rendering.</p>
  </main>
</BaseLayout>
```

- [ ] **Step 4: Update the app README to match the real bootstrap**

Replace `apps/web/README.md` with:

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
```

- [ ] **Step 5: Install dependencies and verify the shell builds**

Run: `npm --prefix apps/web install`
Expected: local `package-lock.json` is created under `apps/web` and install completes without errors.

Run: `npm --prefix apps/web run build`
Expected: PASS and `apps/web/dist/index.html` is generated.

- [ ] **Step 6: Commit the bootstrap**

```bash
git add apps/web
git commit -m "feat: bootstrap astro web shell"
```

### Task 2: Add The Contract-Aligned Content Seam

**Files:**
- Create: `apps/web/src/lib/content/mockDigest.ts`
- Create: `apps/web/src/lib/content/getLatestDigest.ts`
- Create: `apps/web/tests/content/getLatestDigest.test.ts`

**Interfaces:**
- Consumes:
  - `DigestResource` from `@news-digest/shared-types`
- Produces:
  - `export type MockDigestState = "success" | "empty" | "error"`
  - `export type HomepageDigestState = { kind: "success"; digest: DigestResource } | { kind: "empty" } | { kind: "error"; message: string }`
  - `export async function loadHomepageDigest(state?: MockDigestState): Promise<HomepageDigestState>`

- [ ] **Step 1: Write the failing tests for the content seam**

Create `apps/web/tests/content/getLatestDigest.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { loadHomepageDigest } from "../../src/lib/content/getLatestDigest";

describe("loadHomepageDigest", () => {
  it("returns a success state with the latest digest contract", async () => {
    const result = await loadHomepageDigest("success");

    expect(result.kind).toBe("success");
    if (result.kind !== "success") return;

    expect(result.digest.date).toBe("2026-06-24");
    expect(result.digest.entries[0]?.headline).toBe("AI 芯片与模型基础设施继续升温");
  });

  it("returns an empty state when the seam is told to simulate no digest", async () => {
    const result = await loadHomepageDigest("empty");

    expect(result).toEqual({ kind: "empty" });
  });

  it("returns an error state when the seam is told to simulate a failure", async () => {
    const result = await loadHomepageDigest("error");

    expect(result).toEqual({
      kind: "error",
      message: "Unable to load latest digest."
    });
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm --prefix apps/web run test -- tests/content/getLatestDigest.test.ts`
Expected: FAIL because `loadHomepageDigest` does not exist yet.

- [ ] **Step 3: Implement the mock digest and seam**

Create `apps/web/src/lib/content/mockDigest.ts`:

```ts
import type { DigestResource } from "@news-digest/shared-types";

export const MOCK_LATEST_DIGEST: DigestResource = {
  date: "2026-06-24",
  published_at: "2026-06-24T09:00:00Z",
  entries: [
    {
      cluster_id: "cluster-ai-chip-001",
      rank: 1,
      category: "technology",
      headline: "AI 芯片与模型基础设施继续升温",
      summary: "多家厂商围绕训练基础设施与推理部署发布新进展。",
      source_count: 3
    }
  ]
};
```

Create `apps/web/src/lib/content/getLatestDigest.ts`:

```ts
import type { DigestResource } from "@news-digest/shared-types";

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
```

- [ ] **Step 4: Run the seam tests to verify they pass**

Run: `npm --prefix apps/web run test -- tests/content/getLatestDigest.test.ts`
Expected: PASS with 3 tests passing.

- [ ] **Step 5: Commit the content seam**

```bash
git add apps/web/src/lib/content apps/web/tests/content/getLatestDigest.test.ts
git commit -m "feat: add homepage digest content seam"
```

### Task 3: Render The Homepage Success State

**Files:**
- Create: `apps/web/src/components/digest/DigestHeader.astro`
- Create: `apps/web/src/components/digest/DigestEntryList.astro`
- Create: `apps/web/src/components/digest/DigestEntryItem.astro`
- Create: `apps/web/tests/homepage-success.test.ts`
- Modify: `apps/web/src/pages/index.astro`
- Modify: `apps/web/src/styles/global.css`

**Interfaces:**
- Consumes:
  - `BaseLayout.astro`
  - `loadHomepageDigest(state?: MockDigestState): Promise<HomepageDigestState>`
- Produces:
  - `DigestHeader.astro` props: `{ date: string; publishedAt: string }`
  - `DigestEntryList.astro` props: `{ entries: DigestResource["entries"] }`
  - `DigestEntryItem.astro` props: `{ entry: DigestResource["entries"][number] }`

- [ ] **Step 1: Write the failing success-build test**

Create `apps/web/tests/homepage-success.test.ts`:

```ts
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");

describe("homepage success build", () => {
  it("renders the latest digest headline and metadata", () => {
    execSync("npm run build", {
      cwd: appDir,
      stdio: "pipe"
    });

    const html = readFileSync(resolve(appDir, "dist/index.html"), "utf8");

    expect(html).toContain("AI 芯片与模型基础设施继续升温");
    expect(html).toContain("2026-06-24");
    expect(html).toContain("3 sources");
  });
});
```

- [ ] **Step 2: Run the success-build test to verify it fails**

Run: `npm --prefix apps/web run test -- tests/homepage-success.test.ts`
Expected: FAIL because the placeholder homepage does not render digest content yet.

- [ ] **Step 3: Implement the digest components and success-state homepage**

Create `apps/web/src/components/digest/DigestHeader.astro`:

```astro
---
interface Props {
  date: string;
  publishedAt: string;
}

const { date, publishedAt } = Astro.props;
---

<header class="digest-header">
  <p class="digest-kicker">Latest digest</p>
  <h2 class="digest-date">{date}</h2>
  <p class="digest-published">Published {publishedAt}</p>
</header>
```

Create `apps/web/src/components/digest/DigestEntryItem.astro`:

```astro
---
import type { DigestEntryResource } from "@news-digest/shared-types";

interface Props {
  entry: DigestEntryResource;
}

const { entry } = Astro.props;
---

<article class="digest-entry">
  <p class="digest-entry-rank">{entry.rank.toString().padStart(2, "0")}</p>
  <h3 class="digest-entry-headline">{entry.headline}</h3>
  <p class="digest-entry-summary">{entry.summary}</p>
  <p class="digest-entry-meta">{entry.source_count} sources</p>
</article>
```

Create `apps/web/src/components/digest/DigestEntryList.astro`:

```astro
---
import type { DigestResource } from "@news-digest/shared-types";

import DigestEntryItem from "./DigestEntryItem.astro";

interface Props {
  entries: DigestResource["entries"];
}

const { entries } = Astro.props;
---

<div class="digest-entry-list">
  {entries.map((entry) => <DigestEntryItem entry={entry} />)}
</div>
```

Replace `apps/web/src/pages/index.astro` with:

```astro
---
import BaseLayout from "../layouts/BaseLayout.astro";
import DigestEntryList from "../components/digest/DigestEntryList.astro";
import DigestHeader from "../components/digest/DigestHeader.astro";
import { loadHomepageDigest } from "../lib/content/getLatestDigest";

const state = await loadHomepageDigest("success");

if (state.kind !== "success") {
  throw new Error("Task 3 expects a success state homepage.");
}

const { digest } = state;
---

<BaseLayout
  title="News Digest"
  description="Daily international digest with a minimal reading-first homepage."
>
  <main class="page-shell">
    <header class="hero">
      <p class="hero-eyebrow">News Digest V2</p>
      <h1 class="hero-title">Daily international digest</h1>
      <p class="hero-copy">A reading-first homepage for the latest published digest.</p>
    </header>

    <section class="digest-panel" aria-labelledby="latest-digest-heading">
      <DigestHeader date={digest.date} publishedAt={digest.published_at} />
      <DigestEntryList entries={digest.entries} />
    </section>
  </main>
</BaseLayout>
```

Update `apps/web/src/styles/global.css`:

```css
:root {
  color-scheme: light;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f8f6f1;
  color: #1f2328;
  line-height: 1.5;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  background: #f8f6f1;
  color: #1f2328;
}

.page-shell {
  width: min(48rem, calc(100vw - 2rem));
  margin: 0 auto;
  padding: 4rem 0 6rem;
}

.hero {
  margin-bottom: 3rem;
}

.hero-eyebrow,
.digest-kicker,
.digest-published,
.digest-entry-meta,
.digest-entry-rank {
  color: #5c6470;
  font-size: 0.9rem;
  letter-spacing: 0.02em;
}

.hero-title,
.digest-date,
.digest-entry-headline {
  line-height: 1.1;
  font-weight: 650;
}

.hero-title {
  margin: 0.35rem 0 0.75rem;
  font-size: clamp(2.3rem, 7vw, 4.4rem);
}

.hero-copy {
  max-width: 36rem;
  margin: 0;
  color: #3a4048;
}

.digest-panel {
  border-top: 1px solid #d8d2c7;
  padding-top: 1.5rem;
}

.digest-header {
  margin-bottom: 2rem;
}

.digest-date {
  margin: 0.25rem 0;
  font-size: 2rem;
}

.digest-entry-list {
  display: grid;
  gap: 1.5rem;
}

.digest-entry {
  padding-top: 1rem;
  border-top: 1px solid #e2ddd2;
}

.digest-entry-headline {
  margin: 0.3rem 0 0.5rem;
  font-size: 1.5rem;
}

.digest-entry-summary {
  margin: 0 0 0.75rem;
  color: #3a4048;
}
```

- [ ] **Step 4: Run the success-build test to verify it passes**

Run: `npm --prefix apps/web run test -- tests/homepage-success.test.ts`
Expected: PASS with the built homepage containing the digest headline, date, and source count metadata.

- [ ] **Step 5: Commit the success-state homepage**

```bash
git add apps/web/src/pages/index.astro apps/web/src/components/digest apps/web/src/styles/global.css apps/web/tests/homepage-success.test.ts
git commit -m "feat: render homepage latest digest success state"
```

### Task 4: Add Empty And Error States, Config, And Final Verification

**Files:**
- Create: `apps/web/src/components/states/EmptyState.astro`
- Create: `apps/web/src/components/states/ErrorState.astro`
- Create: `apps/web/src/lib/config/site.ts`
- Create: `apps/web/tests/homepage-states.test.ts`
- Modify: `apps/web/src/pages/index.astro`
- Modify: `apps/web/src/styles/global.css`
- Modify: `apps/web/README.md`

**Interfaces:**
- Consumes:
  - `MockDigestState`
  - `HomepageDigestState`
  - `loadHomepageDigest(state?: MockDigestState): Promise<HomepageDigestState>`
- Produces:
  - `export function readMockDigestState(value: string | undefined): MockDigestState`
  - Env contract: `PUBLIC_DIGEST_STATE=success|empty|error`

- [ ] **Step 1: Write the failing tests for empty and error state rendering**

Create `apps/web/tests/homepage-states.test.ts`:

```ts
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const testDir = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(testDir, "..");

function buildAndRead(state: "empty" | "error"): string {
  execSync("npm run build", {
    cwd: appDir,
    env: {
      ...process.env,
      PUBLIC_DIGEST_STATE: state
    },
    stdio: "pipe"
  });

  return readFileSync(resolve(appDir, "dist/index.html"), "utf8");
}

describe("homepage alternate states", () => {
  it("renders an empty-state message", () => {
    const html = buildAndRead("empty");

    expect(html).toContain("No digest published yet.");
  });

  it("renders an error-state message", () => {
    const html = buildAndRead("error");

    expect(html).toContain("Latest digest is temporarily unavailable.");
  });
});
```

- [ ] **Step 2: Run the state tests to verify they fail**

Run: `npm --prefix apps/web run test -- tests/homepage-states.test.ts`
Expected: FAIL because the homepage currently hardcodes the success state.

- [ ] **Step 3: Implement the state components, config reader, and homepage branching**

Create `apps/web/src/components/states/EmptyState.astro`:

```astro
<section class="state-panel" aria-live="polite">
  <h2 class="state-title">No digest published yet.</h2>
  <p class="state-copy">Please check back once the next digest has been prepared.</p>
</section>
```

Create `apps/web/src/components/states/ErrorState.astro`:

```astro
---
interface Props {
  message: string;
}

const { message } = Astro.props;
---

<section class="state-panel" aria-live="polite">
  <h2 class="state-title">Latest digest is temporarily unavailable.</h2>
  <p class="state-copy">{message}</p>
</section>
```

Create `apps/web/src/lib/config/site.ts`:

```ts
import type { MockDigestState } from "../content/getLatestDigest";

export const SITE_TITLE = "News Digest";
export const SITE_DESCRIPTION = "Daily international digest with a minimal reading-first homepage.";

export function readMockDigestState(value: string | undefined): MockDigestState {
  if (value === "empty" || value === "error") {
    return value;
  }

  return "success";
}
```

Replace `apps/web/src/pages/index.astro` with:

```astro
---
import DigestEntryList from "../components/digest/DigestEntryList.astro";
import DigestHeader from "../components/digest/DigestHeader.astro";
import EmptyState from "../components/states/EmptyState.astro";
import ErrorState from "../components/states/ErrorState.astro";
import BaseLayout from "../layouts/BaseLayout.astro";
import { readMockDigestState, SITE_DESCRIPTION, SITE_TITLE } from "../lib/config/site";
import { loadHomepageDigest } from "../lib/content/getLatestDigest";

const state = await loadHomepageDigest(
  readMockDigestState(import.meta.env.PUBLIC_DIGEST_STATE)
);
---

<BaseLayout title={SITE_TITLE} description={SITE_DESCRIPTION}>
  <main class="page-shell">
    <header class="hero">
      <p class="hero-eyebrow">News Digest V2</p>
      <h1 class="hero-title">Daily international digest</h1>
      <p class="hero-copy">A reading-first homepage for the latest published digest.</p>
    </header>

    {
      state.kind === "success" ? (
        <section class="digest-panel" aria-labelledby="latest-digest-heading">
          <DigestHeader date={state.digest.date} publishedAt={state.digest.published_at} />
          <DigestEntryList entries={state.digest.entries} />
        </section>
      ) : state.kind === "empty" ? (
        <EmptyState />
      ) : (
        <ErrorState message={state.message} />
      )
    }
  </main>
</BaseLayout>
```

Append to `apps/web/src/styles/global.css`:

```css
.state-panel {
  border-top: 1px solid #d8d2c7;
  padding-top: 1.5rem;
}

.state-title {
  margin: 0 0 0.5rem;
  font-size: 1.6rem;
  line-height: 1.2;
}

.state-copy {
  margin: 0;
  color: #3a4048;
  max-width: 34rem;
}
```

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

## Mock State Switches

Use `PUBLIC_DIGEST_STATE` to verify homepage states without changing page code:

```bash
PUBLIC_DIGEST_STATE=success npm run dev
PUBLIC_DIGEST_STATE=empty npm run build
PUBLIC_DIGEST_STATE=error npm run build
```
```

- [ ] **Step 4: Run the full verification suite**

Run: `npm --prefix apps/web run test`
Expected: PASS with content seam tests, success build test, and empty/error build tests all green.

Run: `npm --prefix apps/web run check`
Expected: PASS with `astro check` and `vitest run` both green.

- [ ] **Step 5: Commit the final homepage polish**

```bash
git add apps/web/src/components/states apps/web/src/lib/config apps/web/src/pages/index.astro apps/web/src/styles/global.css apps/web/tests/homepage-states.test.ts apps/web/README.md
git commit -m "feat: add homepage empty and error states"
```

## Plan Self-Review

- Spec coverage:
  - Astro skeleton and local startup are covered in Task 1.
  - Contract-aligned mock seam is covered in Task 2.
  - Homepage success rendering and first-pass minimal design are covered in Task 3.
  - Empty/error states and final verification are covered in Task 4.
- Placeholder scan:
  - No `TODO`, `TBD`, "similar to", or hidden follow-up instructions remain.
- Type consistency:
  - The plan consistently uses `DigestResource`, `MockDigestState`, `HomepageDigestState`, and `loadHomepageDigest()`.
  - The homepage never assumes fields not present in the current `DigestEntryResource`.

Plan complete and saved to `docs/superpowers/plans/2026-06-24-web-homepage-latest-digest.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
