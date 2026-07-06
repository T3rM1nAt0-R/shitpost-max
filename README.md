# shitpost-max — the backlog

**Status:** planned — has a concrete "how to actually ship this" starting plan (build the harness once, start with 3 named repos). Triaged from `unprocessed-specs/shitpost-max-backlog.md` 2026-07-06.

*This entry was promoted from a single file to a folder because it now holds sub-specs. The original backlog is preserved below; per-idea details live in the sibling `.md` files in this folder.*

---

*100 fire-and-forget services. Each one is a joke on the outside and a real skill on the inside. The commit count is the punchline; the thing you learn building it is the point.*

Convention for every entry: **a script that produces one unit of output on a tick, appends it, and commits.** The differences are what it computes, what it teaches, and how hard it is. Difficulty: 🟢 trivial · 🟡 real · 🔴 chunky.

---

## 1. Number streams (pi's siblings)
These teach algorithms and the discipline of streaming state instead of recomputing.

1. **pi-spigot** — next digit of π forever, integer-only spigot algorithm. 🟡 *streaming algorithms* — see [specs/pi-spigot.md](./specs/pi-spigot.md)
2. **e-stream** — digits of e via a different series. 🟡 *series expansion*
3. **sqrt2-stream** — digits of √2 by long-division digit extraction. 🟡 *arbitrary precision*
4. **golden-ratio** — digits of φ. 🟢 *continued fractions*
5. **primes-forever** — next prime each tick, incremental sieve. 🟡 *sieve theory, memory tradeoffs*
6. **fibonacci-full** — full Fibonacci numbers, no truncation; watch them explode. 🟢 *bignum*
7. **collatz-explorer** — test next integer's 3n+1 chain, log record-holders. 🟡 *unsolved problems, loop detection*
8. **perfect-numbers** — hunt the next perfect number. 🔴 *number theory, performance*
9. **twin-primes** — log twin prime pairs as found. 🟡 *pattern search*
10. **digits-of-tau** — because π is wrong, obviously. 🟢 *reuse the spigot*
11. **catalan-numbers** — combinatorial sequence stream. 🟢 *combinatorics*
12. **pascal-row** — emit the next row of Pascal's triangle. 🟢 *iterative construction*

## 2. Data loggers (the trojan horses)
Start as commit spam, end as datasets you actually own. These teach API polling, rate limits, error handling, and CSV/JSON persistence.

13. **weather-blr** — Bangalore weather every N minutes → CSV. 🟡 *API polling*
14. **usd-inr** — exchange rate hourly; feeds your FI tracking. 🟡 *financial data*
15. **hn-frontpage** — snapshot Hacker News top titles hourly. 🟡 *scraping, dedup*
16. **crypto-tick** — BTC/ETH price log. 🟢 *public API basics*
17. **aqi-blr** — Bangalore air quality; genuinely useful with a newborn. 🟡 *health data + charts later*
18. **github-trending** — daily trending repos snapshot. 🟡 *your discovery-tool feeder*
19. **npm-downloads** — track a package's daily downloads. 🟢 *ecosystem signals*
20. **reddit-titles** — snapshot a subreddit's hot posts. 🟡 *pagination, auth*
21. **wikipedia-featured** — log the daily featured article. 🟢 *structured scraping*
22. **iss-tracker** — International Space Station lat/long each minute. 🟢 *live API, coordinates*
23. **earthquake-log** — USGS feed of recent quakes. 🟡 *filtering event streams*
24. **spotify-charts** — regional top tracks daily. 🟡 *OAuth, the annoying-but-real kind*
25. **steam-playercount** — concurrent players for a game (game-design relevant). 🟡 *market signal*
26. **gas-prices** or **electricity-tariff** — utility cost over time. 🟢 *personal econ dataset*
27. **rss-firehose** — poll 20 feeds, commit new items. 🟡 *feed parsing, state*
28. **domain-watch** — check if a domain you want dropped yet. 🟢 *WHOIS/DNS*

## 3. Homelab witnesses (Atlas-native)
These are monitoring in a joke costume. They'd genuinely help you run Atlas.

29. **uptime-witness** — ping all 17 services each minute, commit health. 🟡 *health checks* — see [specs/uptime-witness.md](./specs/uptime-witness.md)
30. **disk-canary** — log free space on the i7; catch the disk filling *before* it dies. 🟡 *systemd, alerts*
31. **docker-census** — snapshot running containers + restart counts. 🟡 *Docker API*
32. **cert-watch** — days until each TLS cert expires. 🟡 *cron-worthy real value*
33. **backup-witness** — verify last backup timestamp, commit proof. 🔴 *backup discipline* — see `backup-restic-duplicati.md`, this is a natural fire-and-forget implementation of that spec's restore-drill logging step.
34. **latency-log** — ping time to Cloudflare/your domain. 🟢 *network basics*
35. **temp-log** — CPU temp of the i7 over time. 🟢 *reading /sys, sensors*
36. **tunnel-health** — is the Cloudflare tunnel up? 🟡 *dependency monitoring*
37. **litellm-tokens** — log daily token spend across your models. 🟡 *cost observability*
38. **ram-witness** — memory pressure over time. 🟢 *psutil*

## 4. Systems & DevOps sneaked in
The stuff Mr. Silicon Valley thinks you can't do. Building these *is* the proof.

39. **selfhealing-demo** — a service that crashes on purpose and restarts itself. 🟡 *systemd restart policies*
40. **commit-batcher** — commit every second locally, push every 10 min. 🟡 *commit vs push (the git fluency point)*
41. **log-rotator** — generate logs, rotate + compress them. 🟢 *logrotate, real ops*
42. **healthcheck-endpoint** — tiny HTTP server returning JSON status. 🟡 *web servers from scratch*
43. **cron-vs-timer** — same job as cron AND systemd timer, compare. 🟡 *scheduler internals*
44. **secrets-demo** — read an API key from env, never hardcode. 🟢 *the injection-adjacent hygiene* — see `secrets-management-seam.md`.
45. **retry-with-backoff** — hit a flaky endpoint, log retry behavior. 🟡 *resilience patterns*
46. **rate-limit-lab** — deliberately hit a rate limit, handle the 429 gracefully. 🟡 *the thing everyone gets wrong*
47. **container-of-the-day** — build + run a throwaway Docker image daily. 🔴 *Dockerfile fluency*
48. **git-hook-theater** — pre-commit hooks that lint the shitpost. 🟢 *hooks, CI-adjacent*

## 5. Eval loops & AI rigor (the actual gap)
Turn the criticism into repos. Each one is a real eval loop wearing a clown nose. See `eval-harness.md` for the dedicated version of this idea.

49. **llm-vs-llm** — ask two local models the same question daily, log disagreements. 🟡 *evals in disguise*
50. **prompt-injection-lab** — feed a model adversarial inputs, log which break it. 🔴 *literally learns injection* — see `prompt-injection-quarantine.md`.
51. **hallucination-witness** — ask a model a factual question with a known answer, score it daily. 🟡 *the core eval loop*
52. **regression-canary** — same prompt every day, diff the output over time/model versions. 🟡 *eval loops, versioning*
53. **temperature-lab** — same prompt across temperatures, log variance. 🟢 *model behavior intuition*
54. **token-golf** — shrink a prompt daily while keeping output quality above a bar. 🟡 *eval-gated optimization*
55. **json-mode-witness** — ask for strict JSON, log how often it complies. 🟡 *structured output reliability*
56. **rag-decay** — measure retrieval quality on a fixed question set. 🔴 *the harness he mentioned*
57. **commit-poet** — each commit message = one line of an infinite poem from a local model. 🟢 *local inference + the funniest one* — see [specs/commit-poet.md](./specs/commit-poet.md)
58. **model-diff** — new model drops, run your eval set, commit the scorecard. 🔴 *this is literally the job*

## 6. Game-design flavored (your home turf)
Shitposts that double as design tools. These are the ones that read as *you*.

59. **gacha-oracle** — simulate one gacha pull per tick, log the pity-timer stats. 🟡 *Gambit-adjacent*
60. **loot-table-fuzzer** — random drop each tick, watch the distribution converge. 🟡 *Monte Carlo intuition*
61. **balance-witness** — run one match of a toy auto-battler, log who won. 🔴 *sim-based balancing*
62. **name-generator** — procedural fantasy name per tick. 🟢 *grammars, Markov chains*
63. **dungeon-of-the-day** — generate one procedural map daily. 🟡 *procgen*
64. **economy-sim-tick** — one step of a supply/demand loop, log prices. 🔴 *the Gambit core, isolated*
65. **dice-fairness** — roll your custom dice system, prove it's fair (or isn't). 🟡 *stats, chi-square*
66. **card-shuffler** — shuffle a deck, log entropy; are you *really* shuffling? 🟡 *RNG quality*
67. **playtest-bot** — a dumb agent plays your game once, logs the score. 🔴 *automated playtesting*
68. **meta-tracker** — if you had a live game, snapshot the "meta" daily. 🟡 *live-ops thinking*

## 7. Algorithms & CS you'll actually use
69. **sorting-race** — sort random data with a different algorithm daily, log timings. 🟢 *complexity, felt not memorized*
70. **maze-solver** — generate + solve a maze, log path length. 🟡 *BFS/DFS/A**
71. **compression-lab** — compress the day's log, track ratio. 🟢 *entropy*
72. **hash-collision-hunt** — search for collisions in a weak hash. 🔴 *why crypto matters*
73. **regex-of-the-day** — a generated regex + test cases. 🟢 *the skill everyone fakes*
74. **base-converter** — same number in a new base each tick. 🟢 *number representation*
75. **bloom-filter-demo** — add items, log false-positive rate. 🟡 *probabilistic data structures*
76. **lru-cache-witness** — simulate cache hits/misses on a workload. 🟡 *caching, real perf lever*
77. **graph-of-the-day** — generate a random graph, compute a property. 🟡 *graph theory*
78. **diff-engine** — hand-roll a text diff, commit the algorithm's output. 🔴 *how git itself works*

## 8. Text, language & generative
79. **haiku-daily** — a syllable-counted haiku from a local model. 🟢 *constraints + inference*
80. **markov-nonsense** — train on your own notes, generate one sentence. 🟡 *classic NLP*
81. **word-of-the-day** — pull a rare word + usage. 🟢 *dictionary APIs*
82. **anagram-hunter** — find anagrams in a wordlist. 🟢 *string algorithms*
83. **palindrome-generator** — build a longer palindrome each day. 🟡 *generative constraints*
84. **emoji-summary** — summarize today's HN in 3 emojis via a model. 🟢 *fun eval-of-vibes*
85. **translation-telephone** — round-trip a sentence through 5 languages, log the drift. 🟡 *model behavior, hilarious*
86. **fake-changelog** — generate a plausible changelog for a product that doesn't exist. 🟢 *the peak shitpost*

## 9. Finance & FI-flavored (your motivation)
87. **networth-witness** — log a manual net-worth number, chart the trend. 🟢 *the FI dashboard seed* — see `finance-budgeting-tool.md`'s runway-tracker note.
88. **compound-clock** — show what ₹X becomes at Y% each day; motivational spam. 🟢 *the math of FI, visceral*
89. **fear-greed-index** — snapshot market sentiment daily. 🟡 *external signals*
90. **subscription-audit** — log your recurring costs, shame yourself monthly. 🟢 *actually saves money*
91. **rupee-cost-averaging-sim** — simulate DCA into an index, log the curve. 🟡 *investing intuition*

## 10. Pure satire tier (commit to the bit)
92. **commit-driven-development** — one file, an integer, increments forever. README: "quality is measured in quantity." 🟢
93. **high-iq-certifier** — the origin story. Commits `still high IQ` on a loop. 🟢 — see [specs/high-iq-certifier.md](./specs/high-iq-certifier.md)
94. **green-square-maxxer** — precisely one commit per day per year, a perfect contribution wall. 🟢 *cron precision*
95. **silicon-valley-buzzword-bot** — generates one fresh buzzword daily. 🟢 *the CEO simulator*
96. **10x-engineer** — literally runs 10 other scripts. 🟡 *orchestration joke that's real orchestration*
97. **agile-theater** — auto-generates a standup update for work that didn't happen. 🟢
98. **thought-leader** — posts one LinkedIn-style platitude per day. 🟢 *ghostwriting the enemy*
99. **certificate-mill** — issues you a new fake AI certification daily, PDF and all. 🟡 *sneaks in PDF generation*
100. **shitpost-max-meta** — the service that monitors all 99 others and commits a daily report. 🔴 *the orchestrator; secretly the most valuable repo here*

---

## How to actually ship this
- **Don't build 100.** Build the harness *once* — a base class: `tick() → produce → append → commit`. Every idea becomes a ~20-line plugin. That harness is itself the "do you understand systems" evidence.
- **Start with 3:** `pi-spigot` (algorithm), `uptime-witness` (real Atlas value), `commit-poet` (the funny one). Prove the pattern, then fire-and-forget the rest.
- **#100 is the sleeper.** An orchestrator monitoring 99 services is a legitimate portfolio piece. The joke accidentally becomes the strongest thing in the repo — which is the entire point you're making to that CEO, without saying a word to him.

*The best revenge on "you only know buzzwords" is a self-running system that quietly teaches you the words for real.*
