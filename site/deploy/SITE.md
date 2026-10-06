# shitpostmax.com site record

| Field | Value |
|---|---|
| Public domain | shitpostmax.com (www too) -> Brian :8097, atlas tunnel |
| Dev domain | dev-test.shitpostmax.com -> Brian :8099, Cloudflare Access only (302 to Access login, checked 2026-10-06) |
| Visibility | prod public; dev private (no SEO, analytics or Search Console on dev) |
| Umami website id | 0634c16e-7743-48c0-981e-e6c91cd2692b (created 2026-10-06, no prior site existed) |
| Search Console | sc-domain:shitpostmax.com verified via DNS TXT (created 2026-10-06), owners: niraj.sangani91@gmail.com and gsc-bot; sitemap https://shitpostmax.com/sitemap.xml submitted, 0 errors |
| HTTPS | owned by another thread. Seen 2026-10-06: `http://shitpostmax.com/` and `https://www.shitpostmax.com/` both answer 200 (no 301 to the canonical host) |

## Created vs reused by this change
- Created: Search Console property, DNS TXT record on the zone, Umami website SHITPOSTMAX, JSON-LD WebSite, canonical, sitemap lastmod, Umami loader (inactive until an id is set), deploy/ANALYTICS.md.
- Reused: robots.ts, sitemap.ts, opengraph-image, manifest, not-found (returns a real 404).
