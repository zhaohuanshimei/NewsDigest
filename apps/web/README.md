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

Use `PUBLIC_DIGEST_STATE` to verify homepage states without editing page code:

```bash
PUBLIC_DIGEST_STATE=success npm run dev
PUBLIC_DIGEST_STATE=empty npm run build
PUBLIC_DIGEST_STATE=error npm run build
```
