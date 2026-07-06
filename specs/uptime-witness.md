# uptime-witness

**One-line:** Ping every Atlas service each minute, append the result, and commit — a health log in a joke costume.

**Difficulty:** 🟡 *real*

**What it secretly teaches:** HTTP health checks, Docker/container networking, service discovery, and the difference between "the container is up" and "the service is actually answering."

**Output per tick:** Append one line to `uptime_log.jsonl`:

```json
{"timestamp":"2026-07-06T12:34:56Z","service":"mood","url":"http://localhost:1003/health","status_code":200,"response_ms":12,"ok":true}
```

**Service list source:** Read `/opt/data/tools/deploy/tools.json` at runtime to discover live services and their ports. Skip non-HTTP or non-local services (e.g., `ollama` may need a different probe). Fall back to a small hardcoded list if the registry is unreadable.

**Check method:** Hit `http://localhost:<port>/health` from the i7 host loopback. This avoids the Cloudflare Access layer (which would block an unauthenticated external request) and tests the actual service container.

**Tick cadence:** 60 seconds.

**State files:**
- `uptime_log.jsonl` — raw per-check events.
- `uptime_summary.json` — last-known status for each service, updated in place.

**Commit message convention:** `uptime: 14/14 OK` or `uptime: brief DOWN (502)`.

**Extensions:**
- Track the last N response times and emit a rolling average.
- Alert via ntfy or a simple webhook when a service flips from OK to DOWN.
- Generate a small HTML status page from the summary.
- Record Caddy reload events by watching `caddy.service` status.

**Why this matters:** This is the exact kind of monitoring the homelab needs. The joke is that it looks like commit spam; the value is a persistent, versioned health history.
