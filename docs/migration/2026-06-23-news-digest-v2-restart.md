# News Digest V2 Restart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the current News Digest repository into a legacy branch, then bootstrap a clean `main` for a frontend/backend separated V2 while preserving key design/context docs and a curated set of useful skills.

**Architecture:** Treat the current repository state as the final V1 snapshot. Preserve V1 through a freeze commit, a `legacy/news-digest-v1` branch, and a legacy tag. Rebuild `main` from an orphan branch containing only V2 bootstrap files, curated docs, selected skills, and a new `claude.md`.

**Tech Stack:** Git, shell utilities, Markdown docs, existing `.claude/skills`, existing `.agents/skills`

## Global Constraints

- Do not lose any existing tracked work before the legacy freeze commit.
- Keep the new `main` clean: no V1 application code, caches, or bulky duplicated skill sets.
- Preserve the new UI design sources and prior project-analysis documents in the new environment.
- Keep the new root guidance file named `claude.md`.
- Preserve only a curated subset of high-value project skills; rely on global skills for the rest.

---

### Task 1: Freeze V1

**Files:**
- Modify: current tracked V1 files in repository root
- Create: legacy git branch and tag

**Interfaces:**
- Consumes: current dirty working tree on `main`
- Produces: a committed V1 freeze point available through `legacy/news-digest-v1` and a legacy tag

- [ ] Review `git status` and confirm only intended tracked changes are included in the freeze commit.
- [ ] Commit the current V1 work with a freeze message such as `chore: freeze v1 before v2 restart`.
- [ ] Create branch `legacy/news-digest-v1` from that freeze commit.
- [ ] Create tag `legacy-v1-freeze-2026-06-23` at the same commit.

### Task 2: Stage V2 Keepers

**Files:**
- Create: external temporary staging directory outside the repo
- Copy: `design-demos/`
- Copy: selected docs from `docs/`
- Copy: selected skill directories from `.claude/skills/` and `.agents/skills/`

**Interfaces:**
- Consumes: V1 repository working tree after freeze commit
- Produces: a safe staging area containing every asset that must survive the orphan reset

- [ ] Create a staging directory outside the repo, for example `/private/tmp/news-digest-v2-bootstrap`.
- [ ] Copy UI design assets into staging.
- [ ] Copy analysis and migration-relevant docs into staging.
- [ ] Copy only curated skills into staging.

### Task 3: Create Clean Main

**Files:**
- Create: orphan branch for V2
- Delete: V1 working tree contents from the new orphan branch

**Interfaces:**
- Consumes: frozen V1 repo and staged keeper assets
- Produces: a clean working tree ready for V2 bootstrap

- [ ] Create an orphan branch, for example `main-v2`.
- [ ] Remove all V1 files from the orphan branch working tree except `.git`.
- [ ] Recreate the minimal V2 directory structure.

### Task 4: Bootstrap V2

**Files:**
- Create: `claude.md`
- Create: `README.md`
- Create: `docs/context/`, `docs/design/`, `docs/architecture/`, `docs/migration/`
- Create: `apps/web/`, `services/api/`, `packages/shared-types/`, `packages/ui/`, `infra/`, `scripts/`
- Copy: staged docs, staged skills, staged design assets

**Interfaces:**
- Consumes: clean orphan working tree and staged keeper assets
- Produces: an initial V2 repository bootstrap commit

- [ ] Restore staged keepers into their new locations.
- [ ] Write a new root `claude.md` for V2.
- [ ] Add a bootstrap `README.md` describing V2 direction and repository layout.
- [ ] Keep only curated project skills in `.claude/skills/` and `.agents/skills/`.
- [ ] Commit the bootstrap state with a message such as `chore: bootstrap news-digest v2`.

### Task 5: Promote V2 Branch To Main

**Files:**
- Modify: local git branch references

**Interfaces:**
- Consumes: committed `main-v2` bootstrap
- Produces: local `main` pointing at V2 and `legacy/news-digest-v1` preserving V1

- [ ] Rename `main-v2` to `main`.
- [ ] Verify `legacy/news-digest-v1` still points to the V1 freeze commit.
- [ ] Verify `main` now points to the V2 bootstrap commit.
- [ ] Leave remote update for a later explicit push step if needed.
