# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

News Digest: A daily international news aggregation site with machine translation. Sources from mainstream media RSS feeds (Reuters, BBC, Guardian, NYT, etc.), translated to Chinese, with a minimal, mobile-first static frontend.

**Core Philosophy**: One digest per day, released in the morning. No infinite scroll, no ads, no recommendation algorithms.

## Repository Structure

```
.
├── src/news_digest/       # Python backend
│   ├── cli.py            # CLI entry point (all commands)
│   ├── pipeline.py       # Production pipeline orchestration
│   ├── fetcher.py        # RSS/HTTP fetching
│   ├── ingestion.py      # Feed source ingestion
│   ├── clustering.py     # SimHash-based event clustering
│   ├── digest.py         # Daily digest generation
│   ├── translator.py     # Translation provider interface
│   ├── translation_service.py  # Translation logic
│   ├── digest_export.py  # JSON export for frontend
│   ├── repository.py     # Data access layer
│   ├── models.py         # SQLAlchemy models
│   └── db.py             # Database session management
├── web/                  # Astro frontend
│   ├── src/
│   │   ├── pages/        # Page routes
│   │   ├── components/   # Reusable components
│   │   ├── layouts/      # Base layouts
│   │   ├── lib/          # Utilities (digest reader, RSS)
│   │   └── styles/       # Global CSS
│   └── dist/             # Build output (gitignored)
├── alembic/              # Database migrations
├── config/               # YAML config (sources.yaml)
├── exports/              # JSON exports (mounted in Docker)
├── tests/                # pytest test suite
└── docs/                 # Project documentation
```

## Development Commands

### Backend Development

```bash
# Install dependencies
pip install -e '.[dev]'

# Database migrations
alembic upgrade head                    # Apply all migrations
alembic revision --autogenerate -m "..." # Create new migration
alembic downgrade -1                    # Rollback one step

# Linting & Type Checking
ruff check .                            # Lint
ruff format .                           # Format
mypy src/news_digest                    # Type check

# Run tests
pytest                                  # All tests
pytest tests/test_fetcher.py            # Single file
pytest -k test_fetch_rss                # Single test
pytest --cov=news_digest --cov-report=html  # Coverage report
```

### Frontend Development

```bash
cd web

# Install dependencies
npm install

# Development server
npm run dev                             # http://localhost:4321

# Build & validate
npm run build                           # Static build to dist/
npm run check                           # Type check
npm run test:build                      # Build validation
npm run lighthouse                      # Performance audit
```

### Docker & Deployment

```bash
# Local development
docker compose up -d                    # Start services
docker compose down                     # Stop services
docker compose logs -f api              # View backend logs
docker compose logs -f web              # View frontend logs

# Database in Docker
docker exec -it shared-postgres psql -U news -d news_digest
```

## CLI Commands

The backend exposes a CLI via `python -m news_digest.cli`. All commands are synchronous and log to stdout/stderr.

### Production Pipeline

```bash
# Full pipeline: fetch → cluster → digest → translate → export → webhook
python -m news_digest.cli produce --date 2026-06-17

# Scheduled production (cron)
python -m news_digest.cli produce-schedule --cron "0 6 * * *"
```

### Individual Steps

```bash
# Fetch all sources
python -m news_digest.cli fetch-all --config config/sources.yaml

# Fetch single source
python -m news_digest.cli fetch <url> <name> --lang en

# Clustering & digest generation
python -m news_digest.cli digest --date 2026-06-17 --top-n 20

# Translate digest
python -m news_digest.cli translate-digest --date 2026-06-17 --target-lang zh

# Export to JSON
python -m news_digest.cli export-digest --date 2026-06-17 --output exports/2026-06-17.json

# Crawl article bodies (for articles with missing body)
python -m news_digest.cli crawl --limit 50

# Start scheduled fetching
python -m news_digest.cli schedule --cron "0 */6 * * *"

# Health check HTTP server
python -m news_digest.cli serve-health --host 0.0.0.0 --port 8080
```

### Common Options

- `--date YYYY-MM-DD`: Target date (defaults to today)
- `--config PATH`: Source config YAML (default: `config/sources.yaml`)
- `--threshold N`: SimHash distance threshold for clustering (default: 8)
- `--top-n N`: Number of digest entries (default: 20)
- `--target-lang CODE`: Translation target language (default: `zh`)
- `--no-translate`: Skip translation step
- `--no-export`: Skip JSON export

## Architecture

### Data Flow

```
1. RSS Fetch (fetcher.py)
   ↓
2. Ingestion (ingestion.py) → Articles table
   ↓
3. Clustering (clustering.py) → Clusters + ClusterMembers
   ↓
4. Digest Generation (digest.py) → DailyDigests
   ↓
5. Translation (translation_service.py) → Translations
   ↓
6. Export (digest_export.py) → exports/YYYY-MM-DD.json
   ↓
7. Frontend Build (Astro) → Static HTML
```

### Key Modules

**fetcher.py**: RSS/HTTP client with retries, rate limiting, and User-Agent rotation.

**clustering.py**: SimHash-based event clustering. Articles with similar titles (Hamming distance < threshold) are grouped into clusters representing the same news event.

**digest.py**: Selects top N clusters by a ranking score: `cluster_size × exp(-λ × age_hours)`. Biases toward larger clusters and recent events.

**translation_service.py**: Translates titles and summaries. Caches results in `translations` table to avoid re-translation. Falls back from DeepL → Google Translate on failure.

**digest_export.py**: Exports daily digest to JSON with schema:
```json
{
  "date": "YYYY-MM-DD",
  "target_lang": "zh",
  "generated_at": "ISO8601",
  "entry_count": 20,
  "entries": [
    {
      "rank": 1,
      "cluster_id": 123,
      "article_id": 456,
      "source": "BBC World",
      "original_title": "...",
      "translated_title": "...",
      "original_summary": "...",
      "translated_summary": "...",
      ...
    }
  ]
}
```

**pipeline.py**: Orchestrates the full production workflow. Fetches sources in parallel, clusters articles, generates digest, translates entries, exports JSON, and optionally triggers a webhook (e.g., to rebuild frontend).

### Database Schema

**sources**: RSS feed configurations (url, name, lang, enabled)

**articles**: Fetched articles with SimHash fingerprint and URL hash for deduplication

**translations**: Cached translations (article_id, target_lang, translated_title, translated_summary)

**clusters**: Event clusters (representative_article_id, size, first_seen_at)

**cluster_members**: Many-to-many mapping between articles and clusters

**daily_digests**: Selected entries for each date (date, cluster_id, rank, category)

### Frontend (Astro)

**Build-time data loading**: The frontend reads `exports/YYYY-MM-DD.json` at build time (via `web/src/lib/digest.ts`) and generates static HTML. No runtime API calls.

**Key files**:
- `web/src/lib/digest.ts`: Reads digest JSON from `../exports/` (one level above web/)
- `web/src/pages/index.astro`: Homepage, shows latest digest
- `web/src/pages/archive/[date].astro`: Archive page for specific date
- `web/src/pages/feed.xml.ts`: RSS feed generation

**Build behavior**: During Docker build, `exports/` is copied into the builder container so Astro can read it. The final image contains only the static `dist/` output.

## Environment Variables

Create a `.env` file (or set in Docker):

```bash
# Database (required)
DATABASE_URL=postgresql+psycopg://news:news@localhost:5432/news_digest

# Translation (at least one required for translation)
DEEPL_API_KEY=your-key-here
GOOGLE_TRANSLATE_API_KEY=your-key-here

# Runtime
LOG_LEVEL=INFO
TZ=Asia/Shanghai

# Webhook (optional, for triggering frontend rebuild)
FRONTEND_BUILD_WEBHOOK_URL=https://...

# Frontend (for RSS generation)
SITE_URL=https://news.maczhao.com
```

## Testing Strategy

**Unit tests**: Core logic (SimHash, ranking, translation, clustering)

**Integration tests**: Database operations, fetcher, repository

**CLI tests**: Command execution with mocked dependencies

**Frontend tests**: Build validation (`scripts/verify-build.mjs`), Lighthouse CI

**Coverage target**: ≥ 85% (enforced by `pytest --cov-fail-under=85`)

Run tests before committing:
```bash
pytest                          # Backend
ruff check .                    # Lint
mypy src/news_digest            # Type check
cd web && npm run check         # Frontend type check
```

## Deployment

**Backend**: Runs in Docker on VPS. The `api` service executes `python -m news_digest.cli serve-health` which serves health checks at `/healthz` and `/health.json`.

**Frontend**: Static build deployed via Cloudflare Pages or similar. The `web` service builds with `Dockerfile.web` which:
1. Copies `exports/` directory into build context
2. Runs `npm run build` (Astro reads exports during build)
3. Outputs to `dist/`
4. Serves via nginx

**Reverse proxy**: Caddy routes `news.maczhao.com` → `news-digest-web:80`

**Health monitoring**: `/health.json` returns pipeline status, source health, and alerts.

## Workflow

This project follows a task-based workflow documented in `docs/WORKFLOW.md`:

1. Pick a task from `docs/DEVELOPMENT_PLAN.md`
2. Create a branch: `git checkout -b task/Tx.y-slug`
3. Develop and test locally
4. Commit: `git commit -m "feat(Tx.y): description"`
5. Merge to main: `git merge --no-ff task/Tx.y-slug`
6. Mark task as `[x]` in `DEVELOPMENT_PLAN.md`
7. Commit: `git commit -m "docs: mark Tx.y done"`

**Commit format**: `<type>(Tx.y): <description>`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`

## Key Constraints

1. **No AI-generated summaries**: Only translations. Summaries are from original RSS feeds.

2. **Mobile-first**: Frontend targets mobile devices primarily. Lighthouse score ≥ 95.

3. **Static frontend**: No client-side JavaScript for content rendering. Astro generates pure HTML at build time.

4. **One digest per day**: Released early morning (6 AM). No infinite scroll or real-time updates.

5. **Source reliability**: Only mainstream international news sources (Reuters, BBC, NYT, Guardian, etc.). See `config/sources.yaml`.

6. **Deduplication**: SimHash-based clustering prevents duplicate events from appearing in the same digest.

7. **Minimal dependencies**: Backend uses standard Python libraries where possible. Frontend uses Astro with zero runtime JS.

## Common Tasks

### Adding a new RSS source

1. Edit `config/sources.yaml`:
   ```yaml
   - name: Source Name
     url: https://example.com/rss
     type: rss
     lang: en
     enabled: true
   ```

2. Test: `python -m news_digest.cli fetch <url> "Source Name" --lang en`

3. Add to batch: `python -m news_digest.cli fetch-all`

### Debugging failed translation

Check logs for provider errors. If DeepL fails, the system auto-falls back to Google Translate. Verify API keys in `.env`:

```bash
echo $DEEPL_API_KEY
echo $GOOGLE_TRANSLATE_API_KEY
```

### Regenerating a digest

```bash
# Delete existing digest
docker exec shared-postgres psql -U news -d news_digest \
  -c "DELETE FROM daily_digests WHERE date = '2026-06-17';"

# Regenerate
python -m news_digest.cli digest --date 2026-06-17

# Translate
python -m news_digest.cli translate-digest --date 2026-06-17

# Export
python -m news_digest.cli export-digest --date 2026-06-17
```

### Fixing "exports not found" in frontend build

The frontend reads `../exports/` relative to `web/`. During Docker build, `Dockerfile.web` must `COPY exports/ ../exports/` before running `npm run build`.

If local dev shows "no digest", either:
- Run backend export first: `python -m news_digest.cli export-digest`
- Or set `DIGEST_JSON_PATH=/absolute/path/to/export.json`

### Updating database schema

```bash
# 1. Edit src/news_digest/models.py
# 2. Generate migration
alembic revision --autogenerate -m "add new column"

# 3. Review generated migration in alembic/versions/
# 4. Apply
alembic upgrade head

# In Docker
docker exec news-digest-api alembic upgrade head
```

## Documentation

- `README.md`: Project overview and local setup
- `docs/DEVELOPMENT_PLAN.md`: Phase-by-phase task list with [x] completion tracking
- `docs/WORKFLOW.md`: Git workflow and commit conventions
- `docs/NORTH_STAR_PLAN.md`: Long-term vision and priorities
- `docs/DEPLOYMENT.md`: Deployment runbook
- **`docs/WEBSITE_IMPROVEMENT_PLAN.md`**: 🎯 **Comprehensive website improvement plan** - gap analysis, design principles, 34+ detailed tasks across 7 phases with priorities, timelines, and acceptance criteria. **Start here for frontend improvements.**

## Notes for Future Sessions

1. **The project is deployed on a VPS at 149.104.26.38** with Caddy reverse proxy routing `news.maczhao.com` to `news-digest-web`.

2. **Database must be initialized** with `alembic upgrade head` before first use.

3. **Frontend build requires exports/** directory to be present during build time. `Dockerfile.web` copies it from the host.

4. **Translation is optional**: Use `--no-translate` to skip if API keys are not configured.

5. **Health checks** are exposed at `/healthz` (text) and `/health.json` (structured) by the `serve-health` command.

6. **The production pipeline** (`produce`) is the primary entry point for daily operations. It runs all steps in sequence and can be scheduled via `produce-schedule`.

7. **Extreme minimalism** is a design principle. Avoid adding features, dependencies, or complexity without strong justification.

## Production Server Details

### Server Access
- **IP**: 149.104.26.38
- **SSH**: `ssh root@149.104.26.38`
- **Project directory**: `/www/projects/news-digest`

### Database Configuration
- **Database host**: `shared-postgres` (Docker container)
- **Database name**: `news_digest`
- **Database user**: `news`
- **Database password**: `news`
- **Connection string**: `postgresql+psycopg://news:news@shared-postgres:5432/news_digest`

### Docker Containers
- `news-digest-api`: Backend API service
- `news-digest-web`: Frontend nginx service
- `shared-postgres`: PostgreSQL database (shared with other projects)
- `caddy`: Reverse proxy

### Environment Variables (.env)
The `.env` file on the server contains:
```bash
DATABASE_URL=postgresql+psycopg://news:news@shared-postgres:5432/news_digest
SITE_URL=https://news.maczhao.com
LOG_LEVEL=INFO
TZ=Asia/Shanghai
```

## Google AI Studio Key

### Purpose
Google AI Studio Key (Gemini API) can be used for future translation features. Currently, translation is skipped due to network issues.

### How to Add the Key
1. SSH into the server:
   ```bash
   ssh root@149.104.26.38
   ```

2. Add the key to the `.env` file:
   ```bash
   echo "GOOGLE_AI_KEY=your-key-here" >> /www/projects/news-digest/.env
   ```

3. Restart the API container:
   ```bash
   cd /www/projects/news-digest && docker compose restart api
   ```

### Security Best Practices
- **Never commit API keys to Git**
- The `.env` file is already in `.gitignore`
- The `.env` file permissions are set to 600 (owner read/write only)
- Use different keys for development and production environments

### API Documentation
- Google AI Studio: https://ai.google.dev/gemini-api/docs?hl=zh-cn
- Gemini API supports translation tasks with high quality

## Deployment Workflow

### Updating Code to Production

1. **Commit and push changes locally**:
   ```bash
   git add .
   git commit -m "feat: description"
   git push origin main
   ```

2. **Sync code to server**:
   ```bash
   rsync -avz --exclude '.git' --exclude 'node_modules' --exclude '.venv' \
     /Users/celongzhao/20260424_NewsDigest/ \
     root@149.104.26.38:/www/projects/news-digest/
   ```

3. **Rebuild and restart containers**:
   ```bash
   ssh root@149.104.26.38 "cd /www/projects/news-digest && docker compose down && docker compose up -d --build"
   ```

### Generating Daily News

```bash
ssh root@149.104.26.38 "docker compose -f /www/projects/news-digest/docker-compose.yml exec api python -m news_digest.cli produce --date $(date +%Y-%m-%d) --no-translate"
```

### Updating Frontend After News Generation

**Important**: Use `docker compose up -d web` instead of `docker compose start web` to recreate the container with the new image.

```bash
ssh root@149.104.26.38 "cd /www/projects/news-digest && docker compose up -d web"
```

### Verifying Deployment

```bash
# Check backend health
ssh root@149.104.26.38 "curl -s http://127.0.0.1:8080/healthz"

# Check frontend
curl -I https://news.maczhao.com

# Check RSS page
curl -I https://news.maczhao.com/feed.xml

# Check today's news
curl -s https://news.maczhao.com | grep -o '<time[^>]*>[^<]*</time>' | head -3
```

## Recent Updates (2026-06-18)

### Frontend Improvements
- Added theme switching (light/dark mode)
- Improved RSS page with friendly HTML interface
- Added search functionality with Fuse.js
- Improved navigation and footer
- Added design demos in `design-demos/` directory

### Deployment Fixes
- Fixed database connection string (`shared-postgres` instead of `news-signal-postgres`)
- Fixed frontend update workflow (`docker compose up -d` instead of `docker compose start`)
- Added `.env` file on server with correct configuration

### Current Status
- ✅ Backend deployed and running
- ✅ Frontend deployed and showing today's news
- ✅ Search functionality working (41 entries indexed)
- ✅ RSS page shows friendly HTML interface
- ✅ Translation skipped (--no-translate flag used)
