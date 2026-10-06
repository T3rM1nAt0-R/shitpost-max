# shitpostmax.com site record

| Field | Value |
|---|---|
| Public domain | shitpostmax.com (www too) -> Brian :8097, atlas tunnel |
| Dev domain | dev-test.shitpostmax.com -> Brian :8099, Cloudflare Access only (302 to Access login, checked 2026-10-06) |
| Visibility | prod public; dev private (no SEO, analytics or Search Console on dev) |
| Umami website id | 0634c16e-7743-48c0-981e-e6c91cd2692b (created 2026-10-06, no prior site existed) |
| Search Console | sc-domain:shitpostmax.com verified via DNS TXT (created 2026-10-06), owners: niraj.sangani91@gmail.com and gsc-bot; sitemap https://shitpostmax.com/sitemap.xml submitted, 0 errors |
| HTTPS | Caddy 301s `www` to the apex and `X-Forwarded-Proto: http` to https in one hop; HSTS (max-age=31536000, apex only), nosniff and Referrer-Policy added. Tunnel, DNS and zone settings untouched |

## Created vs reused by this change
- Created: Search Console property, DNS TXT record on the zone, Umami website SHITPOSTMAX, JSON-LD WebSite, canonical, sitemap lastmod, Umami loader (inactive until an id is set), deploy/ANALYTICS.md.
- Reused: robots.ts, sitemap.ts, opengraph-image, manifest, not-found (returns a real 404).
