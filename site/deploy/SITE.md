# shitpostmax.com site record

| Field | Value |
|---|---|
| Public domain | shitpostmax.com (www too) -> Brian :8097, atlas tunnel |
| Dev domain | dev-test.shitpostmax.com -> Brian :8099, Cloudflare Access only (302 to Access login, checked 2026-10-06) |
| Visibility | prod public; dev private (no SEO, analytics or Search Console on dev) |
| Umami website id | not created yet (needs Brian) |
| Search Console | not checked yet (needs Brian): sc-domain:shitpostmax.com, gsc-bot owner, sitemap |
| HTTPS | owned by another thread. Seen 2026-10-06: `http://shitpostmax.com/` and `https://www.shitpostmax.com/` both answer 200 (no 301 to the canonical host) |

## Created vs reused by this change
- Created: JSON-LD WebSite, canonical, sitemap lastmod, Umami loader (inactive until an id is set), deploy/ANALYTICS.md.
- Reused: robots.ts, sitemap.ts, opengraph-image, manifest, not-found (returns a real 404).
