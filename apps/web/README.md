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
