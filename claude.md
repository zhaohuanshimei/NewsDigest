# claude.md

This file is the main guidance document for News Digest V2.

## Project Goal

News Digest V2 is a clean restart of the original project. The new system must be frontend/backend separated, API-first, and suitable for future multi-client expansion.

## Source Of Truth

- Architecture docs: `docs/architecture/`
- Business and migration context: `docs/context/`
- UI direction and design demos: `docs/design/` and `design-demos/`
- Master development plan: `docs/superpowers/plans/2026-06-23-news-digest-v2-master-plan.md`
- Restart execution plan: `docs/migration/2026-06-23-news-digest-v2-restart.md`
- Legacy reference only: `legacy-reference/`

## Architecture Principles

1. API-first, not build-time file coupling.
2. Frontend and backend evolve independently.
3. Preserve content-first and minimal design principles.
4. Reuse ideas from V1, but do not carry over V1 structure blindly.
5. Keep repository root clean and oriented around V2 only.

## Initial Repository Layout

- `apps/web`: frontend app
- `services/api`: backend service
- `packages/shared-types`: shared API/data contracts
- `packages/ui`: reusable UI components and design tokens
- `docs/context`: extracted V1 business logic, database notes, workflow, deployment notes
- `docs/design`: retained UI direction docs
- `docs/architecture`: V2 architecture docs
- `docs/migration`: restart and migration planning docs

## Skills Policy

- Prefer global skills for general-purpose capabilities.
- Keep only a curated subset of project-useful skills in `.claude/skills` and `.agents/skills`.
- Do not bulk-copy full global skill inventories into this repo again.

## Immediate Next Work

1. Define V2 architecture and domain model.
2. Define API and shared types.
3. Rebuild frontend from new UI direction.
4. Rebuild backend around services and publish APIs.
