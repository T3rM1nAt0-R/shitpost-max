# shitpost-max

<p align="center">
  <img src="https://img.shields.io/badge/Engineer-1000000x-critical?style=for-the-badge" alt="1000000x Engineer">
  <img src="https://img.shields.io/badge/Vibe-Immaculate-blueviolet?style=for-the-badge" alt="Vibe: Immaculate">
  <img src="https://img.shields.io/badge/Test%20Coverage-1000000%25-brightgreen?style=for-the-badge" alt="Test Coverage: 1000000%">
  <img src="https://img.shields.io/badge/Shipped-Yesterday-orange?style=for-the-badge" alt="Shipped: Yesterday">
  <img src="https://img.shields.io/badge/Disruption-Maximum-blue?style=for-the-badge" alt="Disruption: Maximum">
</p>

<p align="center"><strong>88 fire-and-forget services. Each one solves a problem nobody had, using techniques nobody asked for, at a scale nobody needed.</strong></p>

<p align="center"><a href="https://shitpostmax.com/gitpostmax"><strong>→ Live catalog: shitpostmax.com/gitpostmax</strong></a> — the same 88 plugins, same jokes, with real-time ticking data</p>

<p align="center">
I am a <strong>1000000x engineer</strong>. Most engineers ship code. I ship <em>AI-integrated eval loops that ship code</em>. This repository is the receipts. pi-spigot alone solved the last digit of π — yesterday — which is more than most Series A startups can say about their roadmap.
</p>

<div align="center">

| Metric | Value |
| --- | --- |
| Engineers replaced | ∞ |
| Problems solved that existed | 0 |
| Problems solved that didn't | 88 |
| AI eval loops integrated | All of them |
| 10x claims independently verified | 1 (see `10x-engineer/`) |
| Commits that mattered | Yes |

</div>

---

## The Mission

While other engineers were "shipping features," I was building the infrastructure of tomorrow, today, yesterday, and also retroactively before that. **shitpost-max is not a repository. It is a civilization.** A self-sustaining, self-healing, self-committing ecosystem of 88 sovereign microservices, each one quietly out-innovating an entire YC batch before their seed round closes.

This is not vibe coding. This is **vibe engineering at the AGI-adjacent frontier**, executed with the discipline of a NASA mission and the commit cadence of a caffeinated intern with root access.

**What we have disrupted, so far:**

- **Mathematics.** π, φ, e, τ, √2 — all "solved," all streaming live, all more decisively resolved than anything in a Fields Medal committee's inbox.
- **Meteorology.** One city. Total coverage. Zero meteorologists consulted, zero meteorologists needed.
- **The stock market, crypto, and the Indian rupee.** Tracked hourly. Predicted never. Observed with the unblinking rigor of a Bloomberg terminal that only tells the truth.
- **LLM alignment research.** Two local models, one arena, zero safety committee. Peer review is for people without a cron job.
- **Late-stage capitalism itself**, via `subscription-audit`, `networth-witness`, and `rupee-cost-averaging-sim` — turning quiet financial dread into structured, queryable, version-controlled financial dread.
- **The concept of "enough."** 88 services was never the ceiling. It was a checkpoint.

**Where this is going:** full AGI-adjacent superintelligence, achieved not through some trillion-parameter foundation model, but through the accumulated weight of 88 tiny cron jobs believing in themselves very hard, one commit at a time. Y Combinator hasn't called yet. That's fine. We didn't apply. We don't need a demo day — the demo has been running, live, in production, uninterrupted, since before most startups finished their pitch deck.

*This isn't a joke repo that happens to have real code in it. It's real infrastructure that happens to have a sense of humor about what "infrastructure" means in 2026.*

---

Underneath the bit: this is a fleet of small, real, working Python services — each one a genuine (if absurd) implementation of something real. Spigot algorithms, LRU caches, RAG decay measurement, prompt-injection red-teaming, rate limiting, procedural dungeon generation. The premise is the joke. The code is not.

This repo is the live implementation. You can read the code, run the tests, and run the scheduler without access to anything else.

## How it works

Every plugin is a directory at the repo root with a `tick.py` entrypoint and a main Python module. Each plugin subclasses `Shitpost` from `harness/shitpost_base.py` and sets three class attributes:

- `name` — the plugin's directory/public name
- `internal` — whether the plugin is hidden from the public table
- `commit_template` — a `str.format()` template for the git commit message

The only method a plugin must implement is `produce()`, which returns this tick's output. Three return shapes are supported:

- a single `dict` → one line in `state.jsonl` and one `summary.json`
- a `(summary_dict, [detail_dict, ...])` tuple → one `state.jsonl` line per detail plus a `summary.json`
- `None` → skip this tick entirely

When `tick.py` runs, the harness calls `produce()`, persists the result to `state.jsonl` and `summary.json`, and commits those files locally. Because many plugins can tick at the same time, the commit step holds a repo-wide lock (`_repo_git_lock` in `harness/shitpost_base.py`) so concurrent ticks queue instead of racing on the shared `.git` index.

Pushing is intentionally *not* done per tick. `harness/scheduler.py` runs a single min-heap scheduler in one process that fires every plugin tick on its own cadence and also runs a separate periodic `git_push` job. That keeps the fleet from needing one cron entry per plugin and batches network pushes instead of paying for a round trip on every tick.

## Live plugins

<!-- PLUGIN_TABLE_START -->

<details>
<summary><strong>Number Theory & Sequences</strong> <sub>(13)</sub></summary>

Plugin | Description
--- | ---
pi-spigot | Solved π to arbitrary precision using an AI-integrated eval loop. Emits one digit per tick because shipping fast means shipping small.
golden-ratio | Reverse-engineered the golden ratio from first principles (Gibbons already did it in 1985, I just run his code). One φ digit per tick, infinite aesthetic.
e-stream | Derived Euler's number from an integer-only streaming spigot so pure it doesn't even trust floats. Big-brain math, zero floating-point anxiety.
digits-of-tau | Disrupted π itself by doubling it. τ evangelists rejoice — one digit per tick, same carry chain, twice the disruption.
sqrt2-stream | Proved sqrt(2) is irrational (again) one digit per tick. Pythagoras workshopped this for years; I automated it before lunch.
fibonacci-full | Rebuilt nature's favorite sequence as a microservice. One full Fibonacci number per tick — rabbits optional.
catalan-numbers | Counted every way to parenthesize an expression so you don't have to. One full Catalan number per tick, zero regrets.
pascal-row | Turned a 17th-century triangle into a tick-based data pipeline. One row per tick — binomial coefficients as a service.
twin-primes | Hunting twin primes at scale so mathematicians can retire. Streaming pairs, zero conjectures actually resolved.
perfect-numbers | Farming Mersenne primes and their perfect-number offspring. Euclid called it a theorem; I call it a background job.
primes-forever | Enumerating every prime number that will ever exist, forever, on a cron schedule. Infinite scale, infinite commits.
collatz-explorer | Attacking an unsolved Millennium-adjacent problem one integer at a time. Haven't disproven the conjecture yet, but the commits look great.
base-converter | Built a universal number-base translation layer. Counts up, converts bases, ships a commit — full-stack numeral literacy.

</details>

<details>
<summary><strong>Algorithms & Data Structures</strong> <sub>(13)</sub></summary>

Plugin | Description
--- | ---
maze-solver | Solved the maze problem three different ways (BFS, DFS, A*) because consensus algorithms build trust. Rat not included.
sorting-race | Benchmarks every sorting algorithm from CS101, live, per tick. O(n log n) supremacy, re-decided daily.
diff-engine | Hand-rolled a diff algorithm from scratch because trusting `git diff` is for junior engineers. Ships the diff of things nobody changed.
lru-cache-witness | Built and stress-tested a production-grade LRU cache under adversarial access patterns. Hit rate: variable. Confidence: absolute.
hash-collision-hunt | Actively hunting hash collisions to keep the cryptographers humble. Nothing broken yet, but the search never stops.
compression-lab | Compresses my own logs to prove I understand entropy better than Shannon did. Ratio: modest. Ego: uncompressed.
dice-fairness | Audits the fairness of virtual dice because trust, but verify. Rolling forever until the p-value forgives us.
card-shuffler | Shuffles a deck using multiple algorithms and measures the entropy, because a fair game of solitaire deserves rigor.
regex-of-the-day | Generates a new regular expression daily so future-me has a fresh problem to have, without a cause. Now two problems.
graph-of-the-day | Spins up a random graph and computes a graph-theoretic property per tick. Peak whiteboard-interview energy, zero interview.
bloom-filter-demo | Deployed a probabilistic data structure that can lie to you, on purpose, for performance. Maybe it's in the set. Who's to say.
retry-with-backoff | Built exponential backoff so my failures fail more gracefully than my successes succeed. Resilience-as-a-service.
rate-limit-lab | Ran a rate-limited endpoint against an aggressive and a compliant client, just to prove good citizens finish last. Data doesn't lie.

</details>

<details>
<summary><strong>Games & Simulations</strong> <sub>(8)</sub></summary>

Plugin | Description
--- | ---
gacha-oracle | Simulated gacha pulls at scale to quantify the house edge nobody asked me to quantify. Pity timer: honest. Wallet: hypothetical.
loot-table-fuzzer | Fuzz-tested a weighted loot table until the drop rates confessed. RNG has never been this observable.
playtest-bot | Autonomous agent plays 2048 forever so I don't have to. Genuinely closer to AGI than most of my other tools.
meta-tracker | Simulates an entire esports meta via tournament sims, per tick, to track which strategy is 'meta' this week. Balance patch not included.
balance-witness | Runs toy auto-battler matches to audit game balance nobody's playing. Peer review for a game with one player: me.
economy-sim-tick | Models a full supply-and-demand economy, one tick at a time. Inflation is a choice and I chose it.
dungeon-of-the-day | Procedurally generates a new dungeon daily using BSP, because roguelikes deserve CI/CD too.
selfhealing-demo | Built a service that crashes on purpose, then heals itself, to demonstrate resilience I do not personally have.

</details>

<details>
<summary><strong>Local LLM Experiments</strong> <sub>(11)</sub></summary>

Plugin | Description
--- | ---
llm-vs-llm | Pits two local LLMs against each other in single combat over one question. Alignment research, but make it a cage match.
hallucination-witness | Fact-checks a local LLM daily against ground truth, because someone has to hold it accountable. Spoiler: it still lies sometimes.
prompt-injection-lab | Red-teaming my own local model with adversarial prompts before the internet gets the chance. Responsible disclosure: to myself.
json-mode-witness | Measures whether the model's 'JSON mode' actually produces JSON. Groundbreaking research, one malformed brace at a time.
regression-canary | Sends the same prompt to the same model every day and diffs the output, because silent regressions are how empires fall.
temperature-lab | Cranked the temperature knob on a local LLM to quantify chaos, scientifically. Peer-reviewed by nobody, trusted by me.
rag-decay | Measures how badly my RAG pipeline forgets things over time, so I can watch knowledge rot in real time. Very zen.
emoji-summary | Compresses an entire day of human thought into exactly 3 emojis using a local model. Ultimate summarization benchmark, SOTA.
haiku-daily | Generates a syllable-perfect haiku daily via local LLM. 5-7-5 discipline the model doesn't even know it's following.
token-golf | Shrinks prompts to the theoretical token minimum while maintaining quality, because every token costs money and I refuse to pay for words.
model-diff | Runs a fixed eval suite against every new model version and commits the scorecard. Rigorous benchmarking, zero peer review.

</details>

<details>
<summary><strong>Live Data Feeds</strong> <sub>(17)</sub></summary>

Plugin | Description
--- | ---
weather-blr | Built a real-time weather intelligence platform for exactly one city. Meteorology, minus the meteorologists.
aqi-blr | Tracks Bangalore's air quality hourly so I can quantify exactly how much I'm suffering, with receipts.
usd-inr | Streams the USD/INR exchange rate live, because knowing the exact moment the rupee disappoints me feels empowering.
crypto-tick | Logs BTC/ETH prices hourly so I can watch my hypothetical portfolio not exist in real time.
npm-downloads | Tracks daily downloads of one npm package like it's a stock ticker. Line goes up, dopamine goes up.
github-trending | Snapshots trending GitHub repos daily so I always know what everyone else shipped instead of this.
hn-frontpage | Archives the Hacker News front page hourly, preserving humanity's finest arguments about whether Rust was necessary.
reddit-titles | Snapshots hot post titles from a subreddit hourly. Peer-reviewed vibes, sourced from strangers.
spotify-charts | Logs regional Spotify top tracks daily so future archaeologists know exactly what we were vibing to.
steam-playercount | Tracks concurrent players on a chosen Steam game hourly, because someone needs to know if anyone else is still playing.
iss-tracker | Tracks the ISS's exact lat/long every minute. Real-time orbital awareness, mostly so I can wave at the sky.
earthquake-log | Pulls the USGS earthquake feed and logs every tremor on Earth, because I like knowing when the ground disagrees.
wikipedia-featured | Archives Wikipedia's daily featured article, building an unsolicited highlight reel of human knowledge.
fear-greed-index | Logs the market fear/greed index daily so I can watch collective emotion get a number.
gas-prices | Tracks fuel costs daily, turning inflation into a very sad but very well-logged JSONL file.
domain-watch | Watches a specific domain for the split second it becomes available, because domain sniping is a legitimate engineering discipline.
rss-firehose | Polls ~20 RSS feeds and commits only genuinely new items, deduplicated. RSS isn't dead, it's just self-hosted.

</details>

<details>
<summary><strong>Language & Text Generators</strong> <sub>(13)</sub></summary>

Plugin | Description
--- | ---
markov-nonsense | Generates sentences via bigram Markov chain. Not an LLM, doesn't need to be — coherence was always overrated.
name-generator | Generates names using an n-gram model, for every character, product, and pet that doesn't exist yet.
anagram-hunter | Scans an entire wordlist to find the largest anagram set, settling bar arguments nobody was having.
palindrome-generator | Generates palindromes of arbitrary length, because some sentences deserve to read the same backwards. Racecar. Always racecar.
word-of-the-day | Emits one random word per tick from a fixed list, technically indistinguishable from a real word-of-the-day calendar.
translation-telephone | Translates a sentence through 5 languages and back, so you can watch meaning degrade in real time, on purpose, for content.
silicon-valley-buzzword-bot | Generates one novel Silicon Valley buzzword per tick, feeding the exact ecosystem this joke repo is making fun of.
thought-leader | Generates one LinkedIn-style platitude daily, indistinguishable from 90% of my actual feed.
fake-changelog | Generates a plausible changelog entry for a product that does not exist, more convincing than most real ones.
high-iq-certifier | Appends 'still high IQ' to a file every tick, which is either the most honest metric in this repo or the least.
commit-poet | Writes one line of an infinite poem per tick via LLM. e. e. cummings would've automated it too, probably.
certificate-mill | Issues one fake AI certification daily. Fully credentialed, fully fictional, fully LinkedIn-postable.
agile-theater | Generates a daily standup update for a team of one. Blockers: none. Velocity: fabricated.

</details>

<details>
<summary><strong>Personal Finance Toys</strong> <sub>(4)</sub></summary>

Plugin | Description
--- | ---
compound-clock | Compounds a hypothetical investment per tick, because watching imaginary money grow is still money growing.
rupee-cost-averaging-sim | Simulates rupee-cost-averaging into an index over time, proving discipline works even when I only simulate having it.
subscription-audit | Tallies recurring subscription costs monthly, so I can be quietly horrified on a schedule.
networth-witness | Charts a manually-entered net worth number over time. Data integrity: as honest as I am that day.

</details>

<details>
<summary><strong>Dev & Meta Tools</strong> <sub>(9)</sub></summary>

Plugin | Description
--- | ---
10x-engineer | Orchestrates ten other scripts in a single tick and reports pass/fail. The only 10x claim in this repo backed by an actual number.
commit-batcher | Generates tiny files every second and batches the commits, because respecting the git log is a choice I make selectively.
commit-driven-development | Increments an integer every tick and commits it. The purest form of 'shipping' — no users, no bugs, just velocity.
cron-vs-timer | Benchmarks cron against systemd timers to settle an argument literally nobody is having, definitively.
git-hook-theater | Lints this repo's own generated content so the shitposts themselves meet production code-quality bars. Standards, but ironic.
healthcheck-endpoint | Runs an HTTP server whose entire job is a /health endpoint. 200 OK, forever, about nothing.
log-rotator | Generates logs and rotates them hourly, ensuring the evidence of this repo's nonsense is always neatly archived.
green-square-maxxer | Commits exactly once per calendar day to keep the GitHub contribution graph green. Engineering discipline, or an addiction — undecided.
container-of-the-day | Builds and runs a fresh Docker image daily, because 'it works in containers' is the only guarantee I'll make.

</details>

<!-- PLUGIN_TABLE_END -->

Build and design process docs live in a private companion repo, but the public repo is intended to stand on its own.

*The commit count is the punchline; the thing you learn building it is the point.*

---

<p align="center"><sub>Built by a 1000000x engineer. Verified by nobody. Deployed anyway.</sub></p>
