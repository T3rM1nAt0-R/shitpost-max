# shitpost-max

100 fire-and-forget services. Each one is a joke on the outside and a real skill on the inside.

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

Plugin | Description
--- | ---
10x-engineer | 
agile-theater | 
anagram-hunter | 
aqi-blr | 
balance-witness | 
base-converter | Base converter plugin: increment a counter and convert it to new bases each tick.
bloom-filter-demo | 
card-shuffler | 
catalan-numbers | 
certificate-mill | 
collatz-explorer | 
commit-batcher | 
commit-driven-development | 
commit-poet | commit-poet plugin: one LLM-generated line of an infinite poem per tick.
compound-clock | 
compression-lab | 
container-of-the-day | 
cron-vs-timer | 
crypto-tick | 
dice-fairness | 
diff-engine | 
digits-of-tau | 
domain-watch | 
dungeon-of-the-day | 
e-stream | 
earthquake-log | 
economy-sim-tick | 
emoji-summary | 
fake-changelog | 
fear-greed-index | 
fibonacci-full | Fibonacci plugin: one full Fibonacci number per tick.
gacha-oracle | 
gas-prices | 
git-hook-theater | 
github-trending | 
golden-ratio | Golden-ratio spigot plugin: one decimal digit of φ per tick.
graph-of-the-day | 
green-square-maxxer | 
haiku-daily | 
hallucination-witness | 
hash-collision-hunt | 
healthcheck-endpoint | 
high-iq-certifier | 
hn-frontpage | 
iss-tracker | 
json-mode-witness | 
llm-vs-llm | 
log-rotator | Cron entry point for the log-rotator plugin.
loot-table-fuzzer | 
lru-cache-witness | 
markov-nonsense | 
maze-solver | 
meta-tracker | 
model-diff | 
name-generator | 
networth-witness | 
npm-downloads | 
palindrome-generator | 
pascal-row | 
perfect-numbers | 
pi-spigot | Pi spigot plugin: one decimal digit of π per tick.
playtest-bot | 
primes-forever | 
prompt-injection-lab | 
rag-decay | 
rate-limit-lab | 
reddit-titles | 
regex-of-the-day | 
regression-canary | 
retry-with-backoff | 
rss-firehose | 
rupee-cost-averaging-sim | 
selfhealing-demo | 
silicon-valley-buzzword-bot | 
sorting-race | 
spotify-charts | 
sqrt2-stream | 
steam-playercount | 
subscription-audit | 
temperature-lab | 
thought-leader | 
token-golf | 
translation-telephone | 
twin-primes | 
usd-inr | 
weather-blr | 
wikipedia-featured | 
word-of-the-day | 

<!-- PLUGIN_TABLE_END -->

Build and design process docs live in a private companion repo, but the public repo is intended to stand on its own.

*The commit count is the punchline; the thing you learn building it is the point.*
