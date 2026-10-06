# shitpostmax.com analytics plan

Umami (https://analytics.nirajsangani.com), one website for `shitpostmax.com`. Public host only:
`dev-test.shitpostmax.com` is Access-only and never loads or counts the snippet
(`src/components/Analytics.tsx` checks the hostname, and `data-domains` is set to the public host).

## Goals
1. Visitors reach the feed and the Meme Mint generator.
2. Visitors follow outbound links to the shipped projects.

## Events
| Event | Trigger | Properties | Goal |
|---|---|---|---|
| `outbound-click` | click on a link to another host | `url` | 2 |
| `scroll-depth` | 25/50/75/100% of the page | `pct` | 1 |
| `404` | the not-found page renders | `path` | health |

No emails, names or free text in properties.

## Funnel
`/` -> `/generator/` -> `outbound-click`

## In Umami (created 2026-10-06)
Goals: "Visit the generator" (path `/generator/`), "Outbound click" (event `outbound-click`), "Scroll depth" (event `scroll-depth`).
Funnel: "Home to generator to outbound click" (30 min window).

## UTM rules
`utm_source` (linkedin, x, youtube, newsletter, github), `utm_medium` (social, email, referral, paid),
`utm_campaign` kebab-case as `<yyyy-mm>-<topic>`.

## Setup
The website id is in `src/lib/analytics.ts`.
Niraj's own visits: run `localStorage.setItem('umami.disabled', 1)` in his browsers.
